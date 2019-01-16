"""
Apply ``coro`` to each emitted value allowing async processing

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()

>>> async def delay_add(a):
...     print('Starting with argument', a)
...     await asyncio.sleep(0.015)
...     result = a + 1
...     print('Finished with argument', a)
...     return result

MODE: CONCURRENT (is default)

>>> _d = s | op.MapAsync(delay_add) | op.Sink()
>>> s.emit(0)
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 0
Starting with argument 1
Finished with argument 0
Finished with argument 1
>>> _d.dispose()

MODE: INTERRUPT

>>> _d = s | op.MapAsync(delay_add, mode=op.MODE.INTERRUPT) | op.Sink(print)
>>> s.emit(0)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.005))
Starting with argument 0
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 1
Finished with argument 1
2
>>> _d.dispose()

MODE: QUEUE

>>> _d = s | op.MapAsync(delay_add, mode=op.MODE.QUEUE) | op.Sink(print)
>>> s.emit(0)
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Starting with argument 0
Finished with argument 0
1
Starting with argument 1
Finished with argument 1
2
>>> _d.dispose()

MODE: LAST

>>> _d = s | op.MapAsync(delay_add, mode=op.MODE.LAST) | op.Sink(print)
>>> s.emit(0)
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

MODE: SKIP

>>> _d = s | op.MapAsync(delay_add, mode=op.MODE.SKIP) | op.Sink(print)
>>> s.emit(0)
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

>>> _d = s | op.MapAsync(delay_add, error_callback=cb) | op.Sink(print)
>>> s.emit('abc')
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument abc
Got error
>>> _d.dispose()
"""
import asyncio
from collections import deque, namedtuple
from enum import Enum
import sys
from functools import wraps
from typing import Any, MutableSequence  # noqa: F401

from broqer import Publisher, default_error_handler, NONE

from .operator import Operator

MODE = Enum('MODE', 'CONCURRENT INTERRUPT QUEUE LAST LAST_DISTINCT SKIP')

_Options = namedtuple('_Options', 'coro mode args kwargs '
                                  'error_callback unpack')


class MapAsync(Operator):
    """ Apply ``coro`` to each emitted value allowing async processing

    :param coro: coroutine to be applied on emit
    :param \\*args: variable arguments to be used for calling coro
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked as (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for calling coro

    :ivar scheduled: Publisher emitting the value when coroutine is actually
        started.
    """
    def __init__(self, coro, *args, mode=MODE.CONCURRENT,
                 error_callback=default_error_handler,
                 unpack: bool = False, **kwargs) -> None:
        """
        mode uses one of the following enumerations:
            - CONCURRENT - just run coroutines concurrent
            - INTERRUPT - cancel running and call for new value
            - QUEUE - queue the value(s) and call after coroutine is finished
            - LAST - use last emitted value after coroutine is finished
            - LAST_DISTINCT - like LAST but only when value has changed
            - SKIP - skip values emitted during coroutine is running
        """
        Operator.__init__(self)
        self._options = _Options(coro, mode, args, kwargs, error_callback,
                                 unpack)
        # ._future is the reference to a running coroutine encapsulated as task
        self._future = None  # type: asyncio.Future

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
        if mode in (MODE.QUEUE, MODE.LAST, MODE.LAST_DISTINCT):
            maxlen = (None if mode is MODE.QUEUE else 1)
            self._queue = deque(maxlen=maxlen)  # type: MutableSequence
        else:  # no queue for CONCURRENT, INTERRUPT and SKIP
            self._queue = None

    def get(self):
        # .get() is not supported for MapAsync
        Publisher.get(self)  # raises ValueError

    def emit_op(self, value: Any, who: Publisher) -> None:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        # check if a coroutine is already running
        if self._future is not None:
            # append to queue if a queue is used in this mode
            if self._queue is not None:
                self._queue.append(value)
                return

            # cancel the future if INTERRUPT mode is used
            if self._options.mode is MODE.INTERRUPT and \
                    not self._future.done():
                self._future.cancel()
            # in SKIP mode just do nothin with this emit
            elif self._options.mode is MODE.SKIP:
                return

        # start the coroutine
        self._run_coro(value)

    def _future_done(self, future):
        """ Will be called when the coroutine is done """
        try:
            # notify the subscribers (except result is an exception or NONE)
            result = future.result()  # may raise exception
            if result is not NONE:
                self.notify(result)  # may also raise exception
        except asyncio.CancelledError:
            return
        except Exception:  # pylint: disable=broad-except
            self._options.error_callback(*sys.exc_info())

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
        if self._options.mode is MODE.LAST_DISTINCT and \
                value == self._last_emit:
            self._future = None
            return

        # store the value to be emitted for LAST_DISTINCT
        self._last_emit = value

        # publish the start of the coroutine
        self.scheduled.notify(value)

        # build the coroutine
        values = value if self._options.unpack else (value,)
        coro = self._options.coro(*values, *self._options.args,
                                  **self._options.kwargs)

        # create a task out of it and add ._future_done as callback
        self._future = asyncio.ensure_future(coro)
        self._future.add_done_callback(self._future_done)


def build_map_async(coro=None, *, mode=None, unpack: bool = False):
    """ Decorator to wrap a coroutine to return a MapAsync operator.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param unpack: value from emits will be unpacked (*value)
    """
    _mode = mode

    def _build_map_async(coro):
        @wraps(coro)
        def _wrapper(*args, mode=None, **kwargs) -> MapAsync:
            if 'unpack' in kwargs:
                raise TypeError('"unpack" has to be defined by decorator')
            if mode is None:
                mode = MODE.CONCURRENT if _mode is None else _mode
            return MapAsync(coro, *args, mode=mode, unpack=unpack, **kwargs)
        return _wrapper

    if coro:
        return _build_map_async(coro)

    return _build_map_async
