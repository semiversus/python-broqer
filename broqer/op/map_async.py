"""
Apply ``map_coro`` to each emitted value allowing async processing

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

Mode: CONCURRENT (is default)

>>> _d = s | op.map_async(delay_add) | op.sink()
>>> s.emit(0)
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 0
Starting with argument 1
Finished with argument 0
Finished with argument 1
>>> _d.dispose()

Mode: INTERRUPT

>>> _d = s | op.map_async(delay_add, mode=op.Mode.INTERRUPT) | op.sink(print)
>>> s.emit(0)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.005))
Starting with argument 0
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 1
Finished with argument 1
2
>>> _d.dispose()

Mode: QUEUE

>>> _d = s | op.map_async(delay_add, mode=op.Mode.QUEUE) | op.sink(print)
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

Mode: LAST

>>> _d = s | op.map_async(delay_add, mode=op.Mode.LAST) | op.sink(print)
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

Mode: SKIP

>>> _d = s | op.map_async(delay_add, mode=op.Mode.SKIP) | op.sink(print)
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

>>> _d = s | op.map_async(delay_add, error_callback=cb) | op.sink(print)
>>> s.emit('abc')
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument abc
Got error
>>> _d.dispose()

Special case if map_coro returns None:

>>> async def foo():
...     pass

>>> _d = s | op.map_async(foo) | op.sink(print, 'EMITTED')
>>> s.emit()
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
EMITTED
>>> _d.dispose()

"""
import asyncio
from collections import deque
from enum import Enum
import sys
from typing import Any, MutableSequence  # noqa: F401

from broqer import Publisher, default_error_handler

from ._operator import Operator, build_operator

Mode = Enum('Mode', 'CONCURRENT INTERRUPT QUEUE LAST LAST_DISTINCT SKIP')


class MapAsync(Operator):
    def __init__(self, publisher: Publisher, map_coro, *args,
                 mode=Mode.CONCURRENT, error_callback=default_error_handler,
                 **kwargs) -> None:
        """
        mode uses one of the following enumerations:
            * CONCURRENT - just run coroutines concurrent
            * INTERRUPT - cancel running and call for new value
            * QUEUE - queue the value(s) and call after coroutine is finished
            * LAST - use last emitted value after coroutine is finished
            * LAST_DISTINCT - like LAST but only when value has changed
            * SKIP - skip values emitted during coroutine is running
        """
        Operator.__init__(self, publisher)
        self._map_coro = map_coro
        self._args = args
        self._kwargs = kwargs
        self._mode = mode
        self._error_callback = error_callback
        self._future = None  # type: asyncio.Future
        self._last_emit = None  # type: Any
        self.scheduled = Publisher()

        if mode in (Mode.QUEUE, Mode.LAST, Mode.LAST_DISTINCT):
            maxlen = (None if mode == Mode.QUEUE else 1)
            self._queue = deque(maxlen=maxlen)  # type: MutableSequence
        else:  # no queue for CONCURRENT, INTERRUPT and SKIP
            self._queue = None

    def get(self):
        return None

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._mode == Mode.INTERRUPT and self._future is not None:
            self._future.cancel()

        if (self._mode in (Mode.INTERRUPT, Mode.CONCURRENT) or
                self._future is None or self._future.done()):

            self._last_emit = args
            self.scheduled.notify(*args)
            future = self._map_coro(*args, *self._args, **self._kwargs)
            self._future = asyncio.ensure_future(future)
            self._future.add_done_callback(self._future_done)
        elif self._mode in (Mode.QUEUE, Mode.LAST, Mode.LAST_DISTINCT):
            self._queue.append(args)

    def _future_done(self, future):
        try:
            result = future.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            self._error_callback(*sys.exc_info())
        else:
            if result is None:
                result = ()
            elif not isinstance(result, tuple):
                result = (result, )
            try:
                self.notify(*result)
            except Exception:
                self._error_callback(*sys.exc_info())

        if self._queue:
            args = self._queue.popleft()  # pylint: disable=E1111
            if self._mode == Mode.LAST_DISTINCT and args == self._last_emit:
                return
            self.scheduled.notify(*args)
            future = self._map_coro(*args, *self._args, **self._kwargs)
            self._future = asyncio.ensure_future(future)
            self._future.add_done_callback(self._future_done)


map_async = build_operator(MapAsync)  # pylint: disable=invalid-name
