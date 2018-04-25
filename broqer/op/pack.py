"""
Emit a multi-argument emit as tuple of arguments

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> _d = s | op.pack() | op.sink(print, 'Packed:')
>>> s.emit(1, 2, 3)
Packed: (1, 2, 3)
"""
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Pack(Operator):
    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._emit(args)


pack = build_operator(Pack)
