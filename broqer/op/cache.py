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
from broqer.publisher import TValue
from broqer.operator import Operator, OperatorFactory


class AppliedCache(Operator):
    """ Cache object applied to publisher (see Map) """
    def __init__(self, publisher: Publisher, init: Any = NONE) -> None:
        Operator.__init__(self, publisher)
        self._state = init

    def get(self) -> TValue:
        return self._orginator.get()

    def emit(self, value: TValue, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        if value != self._state:
            self._state = value
            return Publisher.notify(self, value)

        return None


class Cache(OperatorFactory):  # pylint: disable=too-few-public-methods
    """ Cache emitted values. Suppress duplicated value emits.

    :param init: optional initialization state
    """
    def __init__(self, init: Any = NONE) -> None:
        self._init = init

    def apply(self, publisher: Publisher):
        return AppliedCache(publisher, self._init)
