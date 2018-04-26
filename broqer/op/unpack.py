"""
Unpacking a sequence of values and use it to emit as arguments

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> _d = s | op.unpack() | op.sink(print, 'Unpacked', sep=':')
>>> s.emit( (1, 2, 3) )
Unpacked:1:2:3
"""
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Unpack(Operator):
    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'unpack is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        self._emit(*args[0])


unpack = build_operator(Unpack)
