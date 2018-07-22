"""
Apply ``func`` to the current emitted value and the last result of ``func``

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> def build_number(last_result, value):
...     return last_result*10+value

>>> reduce_publisher = s | op.reduce(build_number)
>>> _d = reduce_publisher | op.sink(print, 'Reduce:')
>>> s.emit(4) # without initialization the first emit is used for this
>>> s.emit(7)
Reduce: 47
>>> s.emit(8)
Reduce: 478
>>> s.emit(1)
Reduce: 4781

Reseting (or just setting) the state is also possible:

>>> reduce_publisher.reset(123)
>>> s.emit(4)
Reduce: 1234
"""
from typing import Any, Callable

from broqer import Publisher, Subscriber

from ._operator import Operator, build_operator
from .accumulate import Accumulate


class Reduce(Accumulate):
    def __init__(self, publisher: Publisher, func: Callable[[Any, Any], Any],
                 init=None) -> None:
        def _func(state, value):
            result = func(state, value)
            return (result, result) # new state and result is the same
        Accumulate.__init__(self, publisher, _func, init)


reduce = build_operator(Reduce)  # pylint: disable=invalid-name
