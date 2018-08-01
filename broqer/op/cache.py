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
    def __init__(self, publisher: Publisher, init: Any=None) -> None:
        Operator.__init__(self, publisher)
        self._state = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)

        old_state = self._state  # to check if .emit was called

        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._publisher.subscribe(self)

        try:
            value = self._publisher.get()
        except ValueError:
            if self._state is not None:
                subscriber.emit(self._state, who=self)
        else:
            if len(self._subscriptions) > 1 or old_state == self._state:
                subscriber.emit(value, who=self)

        return disposable

    def get(self):
        try:
            return self._publisher.get()  # may raise ValueError
        except ValueError:
            return self._state

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._state != value:
            self._state = value
            return self.notify(value)
        return None


cache = build_operator(Cache)  # pylint: disable=invalid-name
