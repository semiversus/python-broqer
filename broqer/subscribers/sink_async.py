"""
Apply ``coro(*args, value, **kwargs)`` to each emitted value allowing async
processing.

Usage:

>>> import asyncio
>>> from broqer import Value, op
>>> s = Value()

>>> async def delay_add(a):
...     print('Starting with argument', a)
...     await asyncio.sleep(0.015)
...     result = a + 1
...     print('Finished with argument', a)
...     return result

MODE: CONCURRENT (is default)

>>> _d = s.subscribe(SinkAsync(delay_add))
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

# pylint: disable=cyclic-import
from broqer import Subscriber, Publisher, default_error_handler
from broqer.op.map_async import AppliedMapAsync, AsyncMode, build_coro


class SinkAsync(Subscriber):  # pylint: disable=too-few-public-methods
    """ Apply ``coro`` to each emitted value allowing async processing

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

        self._dummy_publisher = Publisher()
        _coro = build_coro(coro, unpack, *args, **kwargs)
        self._map_async = AppliedMapAsync(self._dummy_publisher,
                                          _coro,
                                          mode=mode,
                                          error_callback=error_callback)

    def emit(self, value: Any, who: Publisher):
        self._map_async.emit(value, who=self._dummy_publisher)


def build_sink_async(coro=None, *, mode: AsyncMode = AsyncMode.CONCURRENT,
                     unpack: bool = False):
    """ Decorator to wrap a coroutine to return a SinkAsync subscriber.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_sink_async(coro):
        return SinkAsync(coro, mode=mode, unpack=unpack)

    if coro:
        return _build_sink_async(coro)

    return _build_sink_async


def build_sink_async_factory(coro=None, *,
                             mode: AsyncMode = AsyncMode.CONCURRENT,
                             error_callback=default_error_handler,
                             unpack: bool = False):
    """ Decorator to wrap a coroutine to return a factory for SinkAsync
        subscribers.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_sink_async(coro):
        @wraps(coro)
        def _wrapper(*args, **kwargs) -> SinkAsync:
            if ('unpack' in kwargs) or ('mode' in kwargs) or \
                    ('error_callback' in kwargs):
                raise TypeError('"unpack", "mode" and "error_callback" has to '
                                'be defined by decorator')

            return SinkAsync(coro, *args, mode=mode,
                             error_callback=error_callback, unpack=unpack,
                             **kwargs)
        return _wrapper

    if coro:
        return _build_sink_async(coro)

    return _build_sink_async


def sink_async_property(coro=None, *,
                        mode: AsyncMode = AsyncMode.CONCURRENT,
                        error_callback=default_error_handler,
                        unpack: bool = False):
    """ Decorator to build a property returning a SinkAsync subscriber.

    :param coro: coroutine to be wrapped
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked (*value)
    """
    def build_sink_async_property(coro):
        @property
        def _build_sink_async(self):
            return SinkAsync(coro, self, mode=mode,
                             error_callback=error_callback, unpack=unpack)
        return _build_sink_async

    if coro:
        return build_sink_async_property(coro)

    return build_sink_async_property
