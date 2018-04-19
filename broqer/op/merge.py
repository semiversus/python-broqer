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
