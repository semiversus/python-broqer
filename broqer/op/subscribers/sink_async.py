"""
Apply ``coro(*args, value, **kwargs)`` to each emitted value allowing async
processing.

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

>>> _d = s | op.SinkAsync(delay_add)
>>> s.emit(0)
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 0
Starting with argument 1
Finished with argument 0
Finished with argument 1
>>> _d.dispose()
"""

from functools import wraps
from typing import Any

from broqer import Subscriber, Publisher, default_error_handler
from broqer.op import MapAsync, MODE


class SinkAsync(Subscriber):  # pylint: disable=too-few-public-methods
    """ Apply ``coro`` to each emitted value allowing async processing

    :param coro: coroutine to be applied on emit
    :param \\*args: variable arguments to be used for calling coro
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked as (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for calling coro
    """
    def __init__(self, coro, *args, mode=MODE.CONCURRENT,
                 error_callback=default_error_handler,
                 unpack: bool = False, **kwargs) -> None:

        self._map_async = MapAsync(
            coro, *args, mode=mode, error_callback=error_callback,
            unpack=unpack, **kwargs)

    def emit(self, value: Any, who: Publisher):
        self._map_async.emit_op(value, who=None)


def build_sink_async(coro=None, *, mode=None, unpack: bool = False):
    """ Decorator to wrap a coroutine to return a SinkAsync subscriber.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param unpack: value from emits will be unpacked (*value)
    """
    _mode = mode

    def _build_sink_async(coro):
        @wraps(coro)
        def _wrapper(*args, mode=None, **kwargs) -> SinkAsync:
            if 'unpack' in kwargs:
                raise TypeError('"unpack" has to be defined by decorator')
            if mode is None:
                mode = MODE.CONCURRENT if _mode is None else _mode
            return SinkAsync(coro, *args, mode=mode, unpack=unpack, **kwargs)
        return _wrapper

    if coro:
        return _build_sink_async(coro)

    return _build_sink_async
