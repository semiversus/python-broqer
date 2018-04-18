"""
Emit every value delayed by the given time.

Usage:
>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> s | op.delay(0.1) | op.sink(print)
<...>
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.07))
1
2
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
3

"""
import asyncio
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Delay(Operator):
    def __init__(self, publisher: Publisher, delay: float, loop=None) -> None:
        assert delay >= 0, 'delay has to be positive'

        Operator.__init__(self, publisher)

        self._delay = delay
        self._loop = loop or asyncio.get_event_loop()

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._loop.call_later(self._delay, self._emit, *args)


delay = build_operator(Delay)
