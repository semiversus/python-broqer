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

>>> _d = s | op.map_threaded(delay_add) | op.sink()
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

>>> _d = s | op.map_threaded(delay_add, mode=op.Mode.QUEUE) | op.sink(print)
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

>>> _d = s | op.map_threaded(delay_add, mode=op.Mode.LAST) | op.sink(print)
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

>>> _d = s | op.map_threaded(delay_add, mode=op.Mode.SKIP) | op.sink(print)
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

>>> _d = s | op.map_threaded(delay_add, error_callback=cb) | op.sink(print)
>>> s.emit('abc')
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.001))
Starting with argument abc
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Got error
>>> _d.dispose()

Special case if map_func returns None:

>>> def foo(a):
...     pass

>>> _d = s | op.map_threaded(foo, 1) | op.sink(print, 'EMITTED')
>>> s.emit()
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
EMITTED
>>> _d.dispose()

"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from enum import Enum  # noqa: F401
from typing import Any, Callable, MutableSequence  # noqa: F401

from broqer import Publisher, default_error_handler

from ._operator import build_operator
from .map_async import MapAsync, Mode


class MapThreaded(MapAsync):
    def __init__(self, publisher: Publisher, map_func, *args,
                 mode: Mode = Mode.CONCURRENT,  # type: ignore
                 error_callback=default_error_handler, **kwargs) -> None:

        assert mode != Mode.INTERRUPT, 'mode INTERRUPT is not supported'

        MapAsync.__init__(self, publisher, self._thread_coro, mode=mode,
                          error_callback=error_callback)

        if args or kwargs:
            self._map_func = \
               partial(map_func, *args, **kwargs)  # type: Callable
        else:
            self._map_func = map_func  # type: Callable

        self._executor = ThreadPoolExecutor()

    async def _thread_coro(self, *args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._map_func, *args)


map_threaded = build_operator(MapThreaded)  # pylint: disable=invalid-name
