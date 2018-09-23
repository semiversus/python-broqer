"""
Apply ``function`` to the current emitted value and the last result of
``function``.

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

from broqer import NONE

from .accumulate import Accumulate


class Reduce(Accumulate):
    """ Apply ``function`` to the current emitted value and the last result of
    ``function``.

    :param function: function taking the emitted value and the last result of
        the last run.
    :param init: initialisation used as "first result" for the first call of
        ``function`` on first emit.
    """
    def __init__(self, function: Callable[[Any, Any], Any], init: Any) -> None:
        def _function(state, value):
            result = function(state, value)
            return (result, result)  # new state and result is the same
        Accumulate.__init__(self, _function, init)


def build_reduce(function: Callable[[Any, Any], Any] = None, *,
                 init: Any = NONE):
    """ Decorator to wrap a function to return a Reduce operator.

    :param function: function to be wrapped
    :param init: optional initialization for state
    """
    _init = init

    def _build_reduce(function: Callable[[Any, Any], Any]):
        @wraps(function)
        def _wrapper(init=NONE) -> Reduce:
            init = _init if init is NONE else init
            if init is NONE:
                raise TypeError('init argument has to be defined')
            return Reduce(function, init=init)
        return _wrapper

    if function:
        return _build_reduce(function)

    return _build_reduce
