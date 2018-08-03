"""
When this operators gets emitted it's emitting a defined value
"""
import asyncio
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Replace(Operator):
    def __init__(self, publisher: Publisher, value: Any) -> None:
        Operator.__init__(self, publisher)

        self._value = value

    def get(self):
        self._publisher.get()  # may raises ValueError
        return self._value

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who == self._publisher, 'emit from non assigned publisher'
        return self.notify(self._value)


replace = build_operator(Replace)  # pylint: disable=invalid-name
