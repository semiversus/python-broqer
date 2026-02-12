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
import sys
from functools import wraps
from typing import Any  # noqa: F401

# pylint: disable=cyclic-import
from broqer.operator import Operator
from broqer.coro_queue import CoroQueue, AsyncMode, wrap_coro
from broqer import Publisher, default_error_handler, NONE


class MapAsync(Operator):  # pylint: disable=too-many-instance-attributes
    """ Apply ``coro(*args, value, **kwargs)`` to each emitted value allow
    async processing.

    :param coro: coroutine to be applied on emit
    :param \\*args: variable arguments to be used for calling coro
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked as (\\*value)
    :param max_queue_threshold: queue len error threshold,
                                used with AsyncMode.QUEUE
    :param \\*\\*kwargs: keyword arguments to be used for calling coro

    :ivar scheduled: Publisher emitting the value when coroutine is actually
        started.
    """
    def __init__(self,
                 coro, *args, mode=AsyncMode.CONCURRENT,
                 error_callback=default_error_handler, unpack: bool = False,
                 max_queue_threshold: int | None = None, **kwargs) -> None:
        Operator.__init__(self)
        _coro = wrap_coro(coro, unpack, *args, **kwargs)
        self._coro_queue = CoroQueue(
            _coro, mode=mode, max_queue_threshold=max_queue_threshold
        )
        self._error_callback = error_callback

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._originator:
            raise ValueError('Emit from non assigned publisher')

        future = self._coro_queue.schedule(value)
        future.add_done_callback(self._done)

    def _done(self, future: asyncio.Future):
        try:
            result = future.result()
        except Exception:  # pylint: disable=broad-except
            self._error_callback(*sys.exc_info())
        else:
            if result != NONE:
                Publisher.notify(self, result)


def build_map_async(coro=None, *,
                    mode: AsyncMode = AsyncMode.CONCURRENT,
                    error_callback=default_error_handler,
                    unpack: bool = False,
                    max_queue_threshold: int | None = None):
    """ Decorator to wrap a function to return a Map operator.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked (*value)
    :param max_queue_threshold: queue len error threshold,
                                used with AsyncMode.QUEUE
    """
    def _build_map_async(coro):
        return MapAsync(coro, mode=mode, error_callback=error_callback,
                        unpack=unpack, max_queue_threshold=max_queue_threshold)

    if coro:
        return _build_map_async(coro)

    return _build_map_async


def build_map_async_factory(coro=None, *,
                            mode: AsyncMode = AsyncMode.CONCURRENT,
                            error_callback=default_error_handler,
                            unpack: bool = False,
                            max_queue_threshold: int | None = None):
    """ Decorator to wrap a coroutine to return a factory for MapAsync
        operators.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked (*value)
    :param max_queue_threshold: queue len error threshold,
                                used with AsyncMode.QUEUE
    """
    _mode = mode

    def _build_map_async(coro):
        @wraps(coro)
        def _wrapper(*args, mode=None, **kwargs) -> MapAsync:
            if ('unpack' in kwargs) or ('error_callback' in kwargs) or \
                    ('max_queue_threshold' in kwargs):
                raise TypeError(
                    '"unpack", "error_callback" or "max_queue_threshold" '
                    'has to be defined by decorator'
                )
            if mode is None:
                mode = _mode
            return MapAsync(coro, *args, mode=mode, unpack=unpack,
                            error_callback=error_callback,
                            max_queue_threshold=max_queue_threshold, **kwargs)
        return _wrapper

    if coro:
        return _build_map_async(coro)

    return _build_map_async
