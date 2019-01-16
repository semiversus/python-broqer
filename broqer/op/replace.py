"""
Implements the Replace operator
"""
import asyncio
from typing import Any

from broqer import Publisher

from .operator import Operator


class Replace(Operator):
    """ When this operators gets emitted it's emitting a defined value.
    :param value: replacing value to be emitted on emits to this operator
    """
    def __init__(self, value: Any) -> None:
        Operator.__init__(self)
        self._value = value

    def get(self):
        self._publisher.get()  # may raises ValueError
        return self._value

    def emit_op(self, value: Any, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        return self.notify(self._value)
