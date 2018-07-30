"""
>>> from broqer import Subject, op
>>> s = Subject()

>>> cached_publisher = s | op.cache(0)
>>> _disposable = cached_publisher | op.sink(print, sep=' - ')
0

>>> s.emit(3)
3

Also working with multiple arguments in emit:

>>> s.emit(1, 2)
1 - 2
"""
import asyncio
from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Cache(Operator):
    """ Caching the emitted values.

    The ``Cache`` publisher is emitting a value on subscription.

    :param publisher: source publisher
    :param init: initialization for state
    """
    def __init__(self, publisher: Publisher, *init: Any) -> None:
        Operator.__init__(self, publisher)
        if not init:
            self._state = None
        else:
            self._state = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        state = self._state
        self._state = None
        disposable = Operator.subscribe(self, subscriber)
        if len(self._subscriptions) == 1:
            if self._state is None and state is not None:
                self._state = state
                subscriber.emit(*self._state, who=self)  # emit actual cache
        else:
            self._state = state
            if self._state is not None:
                subscriber.emit(*self._state, who=self)
        return disposable

    def get(self):
        if not self._subscriptions:
            args = self._publisher.get()
            if args is None:
                return self._state
            return args
        return self._state

    def emit(self, *args: Any, who: Publisher) -> asyncio.Future:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._state != args:
            self._state = args
            return self.notify(*args)
        return None


cache = build_operator(Cache)  # pylint: disable=invalid-name
