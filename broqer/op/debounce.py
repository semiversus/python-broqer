"""
Emit a value only after a given idle time (emits meanwhile are skipped).
Debounce can also be used for a timeout functionality.

Usage:
>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> s | op.debounce(0.1) | op.sink(print)
<...>
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
3
"""
import asyncio
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Debounce(Operator):
    def __init__(self, publisher: Publisher, duetime: float, loop=None) \
            -> None:
        assert duetime >= 0, 'duetime has to be positive'

        Operator.__init__(self, publisher)

        self._duetime = duetime
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: asyncio.Handle

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._call_later_handler:
            self._call_later_handler.cancel()
        self._call_later_handler = \
            self._loop.call_later(self._duetime, self._emit, *args)


debounce = build_operator(Debounce)
