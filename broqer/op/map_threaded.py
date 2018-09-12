"""
Apply ``map_func`` to each emitted value allowing threaded processing

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

>>> _d = s | op.map_threaded(delay_add) | op.Sink()
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

>>> _d = s | op.map_threaded(delay_add, mode=op.MODE.QUEUE) | op.Sink(print)
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

>>> _d = s | op.map_threaded(delay_add, mode=op.MODE.LAST) | op.Sink(print)
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

>>> _d = s | op.map_threaded(delay_add, mode=op.MODE.SKIP) | op.Sink(print)
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

>>> _d = s | op.map_threaded(delay_add, error_callback=cb) | op.Sink(print)
>>> s.emit('abc')
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument abc
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Got error
>>> _d.dispose()
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Callable  # noqa: F401

from broqer import Publisher, default_error_handler

from .operator import build_operator
from .map_async import MapAsync, MODE


class MapThreaded(MapAsync):
    """ Apply ``map_func`` to each emitted value allowing threaded processing.
    :param publisher: source publisher
    :param map_func: function called to apply
    :param \\*args: variable arguments to be used for calling map_coro
    :param mode: behavior when a value is currently processed
    :param error_callback: error callback to be registered
    :param unpack: value from emits will be unpacked as (*value)
    :param \\**kwargs: keyword arguments to be used for calling map_coro
    """
    def __init__(self, publisher: Publisher, map_func, *args,
                 mode: MODE = MODE.CONCURRENT,  # type: ignore
                 error_callback=default_error_handler,
                 unpack: bool = False, loop=None, **kwargs) -> None:

        assert mode != MODE.INTERRUPT, 'mode INTERRUPT is not supported'

        MapAsync.__init__(self, publisher, self._thread_coro, mode=mode,
                          error_callback=error_callback, unpack=unpack)

        if args or kwargs:
            self._map_func = \
                partial(map_func, *args, **kwargs)  # type: Callable
        else:
            self._map_func = map_func

        self._loop = loop or asyncio.get_event_loop()
        self._executor = ThreadPoolExecutor()

    async def _thread_coro(self, *args):
        return await self._loop.run_in_executor(
            self._executor, self._map_func, *args)


map_threaded = build_operator(MapThreaded)  # pylint: disable=invalid-name
