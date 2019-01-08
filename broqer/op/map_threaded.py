"""
Apply ``function`` to each emitted value allowing threaded processing

Usage:

>>> import time
>>> from broqer import Subject, op
>>> s = Subject()

>>> def delay_add(a):
...     print('Starting with argument', a)
...     time.sleep(0.015)
...     result = a + 1
...     print('Finished with argument', a)
...     return result

Mode: CONCURRENT (is default)

>>> _d = s | op.MapThreaded(delay_add) | op.Sink()
>>> s.emit(0)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument 0
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.03))
Starting with argument 1
Finished with argument ...
Finished with argument ...
>>> _d.dispose()

Mode: QUEUE

>>> _d = s | op.MapThreaded(delay_add, mode=op.MODE.QUEUE) | op.Sink(print)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
>>> s.emit(0)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument 0
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Finished with argument 0
1
Starting with argument 1
Finished with argument 1
2
>>> _d.dispose()

Mode: LAST

>>> _d = s | op.MapThreaded(delay_add, mode=op.MODE.LAST) | op.Sink(print)
>>> s.emit(0)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument 0
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Finished with argument 0
1
Starting with argument 2
Finished with argument 2
3
>>> _d.dispose()

Mode: SKIP

>>> _d = s | op.MapThreaded(delay_add, mode=op.MODE.SKIP) | op.Sink(print)
>>> s.emit(0)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument 0
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Finished with argument 0
1
>>> _d.dispose()

Using error_callback:

>>> def cb(*e):
...     print('Got error')

>>> _d = s | op.MapThreaded(delay_add, error_callback=cb) | op.Sink(print)
>>> s.emit('abc')
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument abc
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Got error
>>> _d.dispose()
"""
import asyncio
from typing import Callable, Any
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps

from broqer import default_error_handler

from .map_async import MapAsync, MODE


class MapThreaded(MapAsync):
    """ Apply ``function`` to each emitted value allowing threaded processing.

    :param function: function called to apply
    :param \\*args: variable arguments to be used for calling function
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked as (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for calling function
    """
    def __init__(self, function: Callable[[Any], Any], *args,
                 mode: MODE = MODE.CONCURRENT,  # type: ignore
                 error_callback=default_error_handler,
                 unpack: bool = False, loop=None, **kwargs) -> None:

        if mode is MODE.INTERRUPT:
            raise ValueError('Mode INTERRUPT is not supported')

        MapAsync.__init__(self, self._thread_coro, mode=mode,
                          error_callback=error_callback, unpack=unpack)

        self._function = partial(function, *args, **kwargs)
        self._loop = loop or asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor()

    async def _thread_coro(self, *args):
        """ Coroutine called by MapAsync. It's wrapping the call of
        run_in_executor to run the synchronous function as thread """
        return await self._loop.run_in_executor(
            self._executor, self._function, *args)


def build_map_threaded(function: Callable[[Any], Any] = None,
                       mode=MODE.CONCURRENT, unpack: bool = False):
    """ Decorator to wrap a function to return a MapThreaded operator.

    :param function: function to be wrapped
    :param mode: behavior when a value is currently processed
    :param unpack: value from emits will be unpacked (*value)
    """
    _mode = mode

    def _build_map_threaded(function: Callable[[Any], Any]):
        @wraps(function)
        def _wrapper(*args, mode=None, **kwargs) -> MapThreaded:
            if 'unpack' in kwargs:
                raise TypeError('"unpack" has to be defined by decorator')
            if mode is None:
                mode = MODE.CONCURRENT if _mode is None else _mode
            return MapThreaded(function, *args, mode=mode, unpack=unpack,
                               **kwargs)
        return _wrapper

    if function:
        return _build_map_threaded(function)

    return _build_map_threaded
