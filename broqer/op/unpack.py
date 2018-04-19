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
