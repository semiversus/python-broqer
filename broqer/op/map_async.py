"""
Apply ``coro`` to each emitted value allowing async processing

Usage:

>>> import asyncio
>>> from broqer import Value, Sink, op
>>> s = Value()

>>> async def delay_add(a):
...     print('Starting with argument', a)
...     await asyncio.sleep(0.015)
...     result = a + 1
...     print('Finished with argument', a)
...     return result

AsyncMode: CONCURRENT (is default)

>>> s.emit(0)
>>> _d = (s | op.MapAsync(delay_add)).subscribe(Sink())
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 0
Starting with argument 1
Finished with argument 0
Finished with argument 1
>>> _d.dispose()

AsyncMode: INTERRUPT

>>> s.emit(0)
>>> o = (s | op.MapAsync(delay_add, mode=op.AsyncMode.INTERRUPT))
>>> _d = o.subscribe(Sink(print))
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.005))
Starting with argument 0
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 1
Finished with argument 1
2
>>> _d.dispose()

AsyncMode: QUEUE

>>> s.emit(0)
>>> o = (s | op.MapAsync(delay_add, mode=op.AsyncMode.QUEUE))
>>> _d = o.subscribe(Sink(print))
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Starting with argument 0
Finished with argument 0
1
Starting with argument 1
Finished with argument 1
2
>>> _d.dispose()

AsyncMode: LAST

>>> s.emit(0)
>>> o = (s | op.MapAsync(delay_add, mode=op.AsyncMode.LAST))
>>> _d = o.subscribe(Sink(print))
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Starting with argument 0
Finished with argument 0
1
Starting with argument 2
Finished with argument 2
3
>>> _d.dispose()

AsyncMode: SKIP

>>> s.emit(0)
>>> o = (s | op.MapAsync(delay_add, mode=op.AsyncMode.SKIP))
>>> _d = o.subscribe(Sink(print))
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Starting with argument 0
Finished with argument 0
1
>>> _d.dispose()

Using error_callback:

>>> def cb(*e):
...     print('Got error')

>>> s.emit('abc')
>>> _d = (s | op.MapAsync(delay_add, error_callback=cb)).subscribe(Sink(print))
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument abc
Got error
>>> _d.dispose()
"""
import asyncio
from collections import deque
from enum import Enum
import sys
from functools import wraps
from typing import Any, MutableSequence, Optional  # noqa: F401

# pylint: disable=cyclic-import
from broqer.operator import Operator, OperatorFactory
from broqer import Publisher, default_error_handler, NONE


def build_coro(coro, unpack, *args, **kwargs):
    """ building a coroutine receiving one argument and call it curried
    with *args and **kwargs and unpack it (if unpack is set)
    """
    if unpack:
        async def _coro(value):
            return await coro(*args, *value, **kwargs)
    else:
        async def _coro(value):
            return await coro(*args, value, **kwargs)

    return _coro


class AsyncMode(Enum):
    """ AyncMode defines how to act when an emit happens while an scheduled
    coroutine is running """
    CONCURRENT = 1  # just run coroutines concurrent
    INTERRUPT = 2  # cancel running and call for new value
    QUEUE = 3  # queue the value(s) and call after coroutine is finished
    LAST = 4  # use last emitted value after coroutine is finished
    LAST_DISTINCT = 5  # like LAST but only when value has changed
    SKIP = 6  # skip values emitted during coroutine is running


class AppliedMapAsync(Operator):
    """ Apply ``coro`` to each emitted value allowing async processing

    :ivar scheduled: Publisher emitting the value when coroutine is actually
        started.
    """
    def __init__(self, publisher: Publisher,
                 coro_with_args, mode=AsyncMode.CONCURRENT,
                 error_callback=default_error_handler,
                 ) -> None:
        Operator.__init__(self, publisher)

        self._coro = coro_with_args
        self._mode = mode
        self._error_callback = error_callback

        # ._future is the reference to a running coroutine encapsulated as task
        self._future = None  # type: Optional[asyncio.Future]

        # ._last_emit is used for LAST_DISTINCT and keeps the last emit from
        # source publisher
        self._last_emit = NONE  # type: Any

        # .scheduled is a Publisher which is emitting the value of the source
        # publisher when the coroutine is actually started
        self.scheduled = Publisher()

        # queue is initialized with following sizes:
        # Mode:                size:
        # QUEUE                unlimited
        # LAST, LAST_DISTINCT  1
        # all others           no queue used
        self._queue = None  # type: Optional[MutableSequence]

        if mode in (AsyncMode.QUEUE, AsyncMode.LAST, AsyncMode.LAST_DISTINCT):
            maxlen = (None if mode is AsyncMode.QUEUE else 1)
            self._queue = deque(maxlen=maxlen)

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        # check if a coroutine is already running
        if self._future is not None:
            # append to queue if a queue is used in this mode
            if self._queue is not None:
                self._queue.append(value)
                return

            # cancel the future if INTERRUPT mode is used
            if self._mode is AsyncMode.INTERRUPT and \
                    not self._future.done():
                self._future.cancel()
            # in SKIP mode just do nothin with this emit
            elif self._mode is AsyncMode.SKIP:
                return

        # start the coroutine
        self._run_coro(value)

    def _future_done(self, future):
        """ Will be called when the coroutine is done """
        try:
            # notify the subscribers (except result is an exception or NONE)
            result = future.result()  # may raise exception
            if result is not NONE:
                Publisher.notify(self, result)  # may also raise exception
        except asyncio.CancelledError:
            return
        except Exception:  # pylint: disable=broad-except
            self._error_callback(*sys.exc_info())

        # check if queue is present and something is in the queue
        if self._queue:
            value = self._queue.popleft()

            # start the coroutine
            self._run_coro(value)
        else:
            self._future = None

    def _run_coro(self, value):
        """ Start the coroutine as task """

        # when LAST_DISTINCT is used only start coroutine when value changed
        if self._mode is AsyncMode.LAST_DISTINCT and \
                value == self._last_emit:
            self._future = None
            return

        # store the value to be emitted for LAST_DISTINCT
        self._last_emit = value

        # publish the start of the coroutine
        self.scheduled.notify(value)

        # build the coroutine
        coro = self._coro(value)

        # create a task out of it and add ._future_done as callback
        self._future = asyncio.ensure_future(coro)
        self._future.add_done_callback(self._future_done)


class MapAsync(OperatorFactory):  # pylint: disable=too-few-public-methods
    """ Apply ``coro(*args, value, **kwargs)`` to each emitted value allow
    async processing.

    :param coro: coroutine to be applied on emit
    :param \\*args: variable arguments to be used for calling coro
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked as (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for calling coro
    """
    def __init__(self, coro, *args, mode=AsyncMode.CONCURRENT,
                 error_callback=default_error_handler,
                 unpack: bool = False, **kwargs) -> None:
        self._coro = build_coro(coro, unpack, *args, **kwargs)
        self._mode = mode
        self._error_callback = error_callback
        self._unpack = unpack

    def apply(self, publisher: Publisher):
        return AppliedMapAsync(publisher,
                               coro_with_args=self._coro,
                               mode=self._mode,
                               error_callback=self._error_callback,
                               )


def build_map_async(coro=None, *,
                    mode: AsyncMode = AsyncMode.CONCURRENT,
                    error_callback=default_error_handler,
                    unpack: bool = False):
    """ Decorator to wrap a function to return a Map operator.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_map_async(coro):
        return MapAsync(coro, mode=mode, error_callback=error_callback,
                        unpack=unpack)

    if coro:
        return _build_map_async(coro)

    return _build_map_async


def build_map_async_factory(coro=None, *,
                            mode: AsyncMode = AsyncMode.CONCURRENT,
                            error_callback=default_error_handler,
                            unpack: bool = False):
    """ Decorator to wrap a coroutine to return a factory for MapAsync
        operators.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked (*value)
    """
    _mode = mode

    def _build_map_async(coro):
        @wraps(coro)
        def _wrapper(*args, mode=None, **kwargs) -> MapAsync:
            if ('unpack' in kwargs) or ('error_callback' in kwargs):
                raise TypeError('"unpack" and "error_callback" has to '
                                'be defined by decorator')
            if mode is None:
                mode = _mode
            return MapAsync(coro, *args, mode=mode, unpack=unpack,
                            error_callback=error_callback, **kwargs)
        return _wrapper

    if coro:
        return _build_map_async(coro)

    return _build_map_async
