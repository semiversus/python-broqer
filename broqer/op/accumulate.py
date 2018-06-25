"""
Call a function with state and new value which is returning new state and value
to emit.

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> def moving_average(state, value):
...     state=state[1:]+[value]
...     return state, sum(state)/len(state)

>>> lowpass = s | op.accumulate(moving_average, init=[0]*3)
>>> lowpass | op.sink(print)
<...>
>>> s.emit(3)
1.0
>>> s.emit(3)
2.0
>>> s.emit(3)
3.0
>>> s.emit(3)
3.0

Reseting (or just setting) the state is also possible:

>>> lowpass.reset([1, 1, 1])
>>> s.emit(4)
2.0

"""
from typing import Any, Callable, Tuple

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Accumulate(Operator):
    def __init__(self, publisher: Publisher,
                 func: Callable[[Any, Any], Tuple[Any, Any]], init) -> None:
        Operator.__init__(self, publisher)
        self._acc_func = func
        self._state = init

    def reset(self, state):
        self._state = state

    def emit(self, arg: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._state, result = self._acc_func(self._state, arg)
        self.notify(result)


accumulate = build_operator(Accumulate)
