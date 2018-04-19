from typing import Any
from operator import getitem

from broqer import Publisher

from ._operator import Operator, build_operator


class Pluck(Operator):
    def __init__(self, publisher: Publisher, *picks: Any) -> None:
        assert len(picks) >= 1, 'need at least one pick key'
        Operator.__init__(self, publisher)

        self._picks = picks

    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'pluck is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        arg = args[0]
        for pick in self._picks:
            arg = getitem(arg, pick)
        self._emit(arg)


pluck = build_operator(Pluck)
