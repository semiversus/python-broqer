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


class Reduce(Operator):
    def __init__(self, publisher: Publisher, func: Callable[[Any, Any], Any],
                 init=None) -> None:
        Operator.__init__(self, publisher)
        self._last_state = init
        self._init = init

        self._reduce_func = func

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Operator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._last_state = self._init

    def get(self) -> Any:
        if not self._subscriptions:
            if self._init is None:
                return
            args = self._publisher.get()
            if args is None:
                return None
            assert len(args) == 1, \
                'reduce is only possible for emits with one argument'
            return (self._reduce_func(self._init, args[0]),)
        if self._last_state is not None:
            return (self._reduce_func(self._last_state, args[0]),)
        return None

    def reset(self, init):
        self._last_state = init

    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'reduce is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._last_state is not None:
            self._last_state = self._reduce_func(self._last_state, args[0])
            self.notify(self._last_state)
        else:
            self._last_state = args[0]


reduce = build_operator(Reduce)  # pylint: disable=invalid-name
