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

    def get(self):
        for p in self._publishers:
            result = p.get()
            if result is not None:
                return result
        return None

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who in self._publishers, 'emit from non assigned publisher'
        return self.notify(*args)


merge = build_operator(Merge)  # pylint: disable=invalid-name
