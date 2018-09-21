"""
Apply ``func`` to the current emitted value and the last result of ``func``

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> def build_number(last_result, value):
...     return last_result*10+value

>>> reduce_publisher = s | op.Reduce(build_number, 0)
>>> _d = reduce_publisher | op.Sink(print, 'Reduce:')
>>> s.emit(4)
Reduce: 4
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
from functools import wraps

from .accumulate import Accumulate


class Reduce(Accumulate):
    """ Apply ``func`` to the current emitted value and the last result of
    ``func``.

    :param func: function taking the emitted value and the last result of the
        last run.
    :param init: initialisation used as "first result" for the first call of
        ``func`` on first emit.
    """
    def __init__(self, func: Callable[[Any, Any], Any], init: Any) -> None:
        def _func(state, value):
            result = func(state, value)
            return (result, result)  # new state and result is the same
        Accumulate.__init__(self, _func, init)


def reduce(function):
    @wraps(function)
    def _wrapper(init: Any):
        return Reduce(function, init)
    return _wrapper
