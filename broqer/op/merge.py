"""
Merge emits of multiple publishers into one stream

Usage:

>>> from broqer import Subject, op
>>> s1 = Subject()
>>> s2 = Subject()

>>> _d = s1 | op.merge(s2) | op.sink(print, 'Merge:')
>>> s1.emit(1)
Merge: 1
>>> s2.emit('abc')
Merge: abc
"""
import asyncio
from typing import Any

from broqer import Publisher

from ._operator import MultiOperator, build_operator


class Merge(MultiOperator):
    def __init__(self, *publishers: Publisher) -> None:
        MultiOperator.__init__(self, *publishers)

    def get(self):
        for publisher in self._publishers:
            try:
                return publisher.get()
            except ValueError:
                pass
        Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who in self._publishers, 'emit from non assigned publisher'
        return self.notify(value)


merge = build_operator(Merge)  # pylint: disable=invalid-name
