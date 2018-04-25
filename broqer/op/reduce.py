"""
Apply ``func`` to the current emitted value and the last result of ``func``

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> def build_number(last_result, value):
...     return last_result*10+value

>>> reduce_publisher = s | op.reduce(build_number)
>>> _d = reduce_publisher | op.sink(print, 'Reduce:')
>>> s.emit(4) # without initialisation the first emit is used for this
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
>>> reduce_publisher.state
1234
"""
from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Reduce(Operator):
    def __init__(self, publisher: Publisher, func: Callable[[Any, Any], Any],
                 init=None) -> None:
        Operator.__init__(self, publisher)
        self._cache = init

        self._reduce_func = func

    def reset(self, init):
        self._cache = init

    @property
    def state(self):
        return self._cache

    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'reduce is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._cache is not None:
            self._cache = self._reduce_func(self._cache, args[0])
            self._emit(self._cache)
        else:
            self._cache = args[0]


reduce = build_operator(Reduce)
