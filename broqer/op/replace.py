"""
When this operators gets emitted it's emitting a defined value
"""

from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Replace(Operator):
    def __init__(self, publisher: Publisher, *args: Any) -> None:
        Operator.__init__(self, publisher)

        self._args = args

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self.notify(self._args)


replace = build_operator(Replace)  # pylint: disable=invalid-name
