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

MODE: CONCURRENT (is default)

>>> _d = s | op.map_async(delay_add) | op.sink()
>>> s.emit(0)
>>> s.emit(1)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
Starting with argument 0
Starting with argument 1
Finished with argument 0
Finished with argument 1
>>> _d.dispose()

MODE: INTERRUPT

>>> _d = s | op.map_async(delay_add, mode=op.MODE.INTERRUPT) | op.sink(print)
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

>>> _d = s | op.map_async(delay_add, mode=op.MODE.QUEUE) | op.sink(print)
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

>>> _d = s | op.map_async(delay_add, mode=op.MODE.LAST) | op.sink(print)
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

>>> _d = s | op.map_async(delay_add, mode=op.MODE.SKIP) | op.sink(print)
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
"""
import asyncio
from collections import deque, namedtuple
from enum import Enum
import sys
from typing import Any, MutableSequence  # noqa: F401

from broqer import Publisher, default_error_handler

from .operator import Operator, build_operator

MODE = Enum('MODE', 'CONCURRENT INTERRUPT QUEUE LAST LAST_DISTINCT SKIP')

_Options = namedtuple('_Options', 'map_coro mode args kwargs '
                                  'error_callback unpack')


class MapAsync(Operator):
    def __init__(self, publisher: Publisher, map_coro, *args,
                 mode=MODE.CONCURRENT, error_callback=default_error_handler,
                 unpack=False, **kwargs) -> None:
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
        self._options = _Options(map_coro, mode, args, kwargs, error_callback,
                                 unpack)
        self._future = None  # type: asyncio.Future
        self._last_emit = None  # type: Any
        self.scheduled = Publisher()

        if mode in (MODE.QUEUE, MODE.LAST, MODE.LAST_DISTINCT):
            maxlen = (None if mode == MODE.QUEUE else 1)
            self._queue = deque(maxlen=maxlen)  # type: MutableSequence
        else:  # no queue for CONCURRENT, INTERRUPT and SKIP
            self._queue = None

    def get(self):
        Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> None:
        assert who is self._publisher, 'emit from non assigned publisher'
        if self._options.mode == MODE.INTERRUPT and self._future is not None:
            self._future.cancel()

        if (self._options.mode in (MODE.INTERRUPT, MODE.CONCURRENT) or
                self._future is None or self._future.done()):

            self._last_emit = value
            self.scheduled.notify(value)
            if self._options.unpack:
                coro = self._options.map_coro(*value, *self._options.args,
                                              **self._options.kwargs)
            else:
                coro = self._options.map_coro(value, *self._options.args,
                                              **self._options.kwargs)
            self._future = asyncio.ensure_future(coro)
            self._future.add_done_callback(self._future_done)
        elif self._options.mode in (MODE.QUEUE, MODE.LAST, MODE.LAST_DISTINCT):
            self._queue.append(value)

    def _future_done(self, future):
        try:
            result = future.result()
        except asyncio.CancelledError:
            pass
        except Exception:  # pylint: disable=broad-except
            self._options.error_callback(*sys.exc_info())
        else:
            try:
                self.notify(result)
            except Exception:  # pylint: disable=broad-except
                self._options.error_callback(*sys.exc_info())

        if self._queue:
            value = self._queue.popleft()  # pylint: disable=E1111
            if self._options.mode == MODE.LAST_DISTINCT and \
                    value == self._last_emit:
                return
            self.scheduled.notify(value)
            if self._options.unpack:
                future = self._options.map_coro(*value, *self._options.args,
                                                **self._options.kwargs)
            else:
                future = self._options.map_coro(value, *self._options.args,
                                                **self._options.kwargs)
            self._future = asyncio.ensure_future(future)
            self._future.add_done_callback(self._future_done)


map_async = build_operator(MapAsync)  # pylint: disable=invalid-name
