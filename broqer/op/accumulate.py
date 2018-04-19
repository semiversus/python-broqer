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
>>> lowpass.state
[3, 3, 3]

Reseting (or just setting) the state is also possible:

>>> lowpass.reset([1, 1, 1])
>>> s.emit(4)
2.0

"""
from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Accumulate(Operator):
    def __init__(self, publisher: Publisher, func: Callable[[Any, Any], Any],
                 init) -> None:
        Operator.__init__(self, publisher)
        self._acc_func = func
        self._state = init

    def reset(self, state):
        self._state = state

    @property
    def state(self):
        return self._state

    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'reduce is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        self._state, result = self._acc_func(self._state, args[0])
        self._emit(result)


accumulate = build_operator(Accumulate)
