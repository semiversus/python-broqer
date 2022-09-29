"""
Cache the latest emit - the result is suppressing multiple emits with the same
value. Also initialization can be defined in the case the source publisher does
not emit on subscription.

Usage:

>>> from broqer import Value, op, Sink
>>> s = Value(1)

>>> cached_publisher = s | op.Cache()
>>> _disposable = cached_publisher.subscribe(Sink(print))
1
>>> s.emit(2)
2
>>> s.emit(2)
>>> _disposable.dispose()

Using the initial value for cache:

>>> from broqer import Value, op, Sink
>>> s = Value()

>>> cached_publisher = s | op.Cache(1)
>>> _disposable = cached_publisher.subscribe(Sink(print))
1
>>> s.emit(1)
>>> s.emit(2)
2
>>> _disposable.dispose()
"""
from typing import Any

from broqer import Publisher, NONE
from broqer.publisher import ValueT
from broqer.operator import Operator


class Cache(Operator):
    """ Cache object applied to publisher (see Map) """
    def __init__(self, init: Any = NONE) -> None:
        Operator.__init__(self)
        self._state = init

    def get(self) -> ValueT:
        if self._originator is None:
            raise ValueError('Operator is missing originator')

        return self._originator.get()

    def emit(self, value: ValueT, who: Publisher) -> None:
        if who is not self._originator:
            raise ValueError('Emit from non assigned publisher')

        if value != self._state:
            self._state = value
            return Publisher.notify(self, value)

        return None
