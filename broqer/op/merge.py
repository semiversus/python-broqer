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
from typing import Any

from broqer import Publisher

from ._operator import MultiOperator, build_operator


class Merge(MultiOperator):
    def __init__(self, *publishers: Publisher) -> None:
        MultiOperator.__init__(self, *publishers)

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who in self._publishers, 'emit from non assigned publisher'
        self._emit(*args)


merge = build_operator(Merge)
