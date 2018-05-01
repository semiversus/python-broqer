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
Starting with argument 0
>>> s.emit(1)
Starting with argument 1
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Finished with argument 0
Finished with argument 1
>>> _d.dispose()

Mode: QUEUE
>>> _d = s | op.map_threaded(delay_add, mode=op.Mode.QUEUE) | op.sink(print)
>>> s.emit(0)
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
Starting with argument 0
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.04))
Finished with argument 0
1
>>> _d.dispose()

Using error_callback:
>>> def cb(e):
...     print('Got error')

>>> _d = s | op.map_threaded(delay_add, error_callback=cb) | op.sink(print)
>>> s.emit('abc')
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
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any, Callable, MutableSequence  # noqa: F401

from broqer import Publisher

from ._operator import Operator, build_operator
from .map_async import Mode


class MapThreaded(Operator):
    def __init__(self, publisher: Publisher, map_func, *args,
                 mode=Mode.CONCURRENT, error_callback=None, **kwargs) -> None:
        """
        mode uses one of the following enumerations:
            * CONCURRENT - just run coroutines concurrent
            * QUEUE - queue the value(s) and call after coroutine is finished
            * LAST - use last emitted value after coroutine is finished
            * SKIP - skip values emitted during coroutine is running
            ( INTERRUPT like MapAsync is not possible with MapThreaded )
        """
        Operator.__init__(self, publisher)
        assert mode != Mode.INTERRUPT, 'mode INTERRUPT is not supported'
        self._mode = mode
        self._error_callback = error_callback
        self._future = None  # type: asyncio.Future

        if args or kwargs:
            self._map_func = \
                partial(map_func, *args, **kwargs)  # type: Callable
        else:
            self._map_func = map_func  # type: Callable

        if mode in (Mode.QUEUE, Mode.LAST):
            self._queue = deque(maxlen=(None if mode == Mode.QUEUE else 1)
                                )  # type: MutableSequence
        else:  # no queue for CONCURRENT and SKIP
            self._queue = None

        if mode == Mode.CONCURRENT:
            workers = None
        else:
            workers = 1

        self._executor = ThreadPoolExecutor(max_workers=workers)

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'

        if (self._mode == Mode.CONCURRENT or
                self._future is None or
                self._future.done()):

                self._future = asyncio.ensure_future(
                    asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._map_func,
                        *args
                    )
                )
                self._future.add_done_callback(self._future_done)
        elif self._mode in (Mode.QUEUE, Mode.LAST):
            self._queue.append(args)

    def _future_done(self, future):
        try:
            result = future.result()
        except Exception as e:
            if self._error_callback is not None:
                self._error_callback(e)
        else:
            if result is None:
                result = ()
            elif not isinstance(result, tuple):
                result = (result, )
            self._emit(*result)

        if self._queue:
            self._future = asyncio.ensure_future(
                asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        self._map_func,
                        *self._queue.popleft()
                )
            )
            self._future.add_done_callback(self._future_done)


map_threaded = build_operator(MapThreaded)
