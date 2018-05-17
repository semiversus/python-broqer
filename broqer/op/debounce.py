"""
Emit a value only after a given idle time (emits meanwhile are skipped).
Debounce can also be used for a timeout functionality.

Usage:
>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> _d = s | op.debounce(0.1) | op.sink(print)
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
3
>>> _d.dispose()

When debounce is retriggered you can specify a value to emit:
>>> debounce_publisher = s | op.debounce(0.1, False)
>>> _d = debounce_publisher | op.sink(print)
>>> s.emit(False)
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
False
>>> s.emit(True)
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(False)
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(True)
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
True

Reseting is also possible:
>>> s.emit(False)
False
>>> s.emit(True)
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> debounce_publisher.reset()
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))

>>> _d.dispose()
"""
import asyncio
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Debounce(Operator):
    def __init__(self, publisher: Publisher, duetime: float,
                 *retrigger_value: Any, loop=None) -> None:
        assert duetime >= 0, 'duetime has to be positive'

        Operator.__init__(self, publisher)

        self.duetime = duetime
        self._retrigger_value = retrigger_value
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: asyncio.Handle

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._retrigger_value:  # if retrigger_value is not empty tuple
            self._emit(*self._retrigger_value)
        if self._call_later_handler:
            self._call_later_handler.cancel()
        self._call_later_handler = \
            self._loop.call_later(self.duetime, self._emit, *args)

    def reset(self):
        if self._retrigger_value:  # if retrigger_value is not empty tuple
            self._emit(*self._retrigger_value)
        if self._call_later_handler:
            self._call_later_handler.cancel()


debounce = build_operator(Debounce)
