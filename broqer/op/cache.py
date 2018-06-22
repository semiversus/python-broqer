"""
Caching the emitted values to access it via ``.state`` property.

The ``Cache`` publisher is emitting a value on subscription.

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> cached_publisher = s | op.cache(0)
>>> _disposable = cached_publisher | op.sink(print, sep=' - ')
0

>>> s.emit(3)
3
>>> cached_publisher.state
3

Also working with multiple arguments in emit:

>>> s.emit(1, 2)
1 - 2
>>> cached_publisher.state
(1, 2)
"""

from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Cache(Operator):
    def __init__(self, publisher: Publisher, *init: Any) -> None:
        Operator.__init__(self, publisher)
        assert len(init) >= 1, 'need at least one argument for cache init'
        self._state = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        cache = self._state  # replace self._state temporary with None
        self._state = None
        disposable = super().subscribe(subscriber)
        if self._state is None:
            # if subscriber was not emitting on subscription
            self._state = cache  # set self._state back
            subscriber.emit(*self._state, who=self)  # and emit actual cache
        return disposable

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._state = args
        self.notify(*args)

    @property
    def state_raw(self):
        return self._state


cache = build_operator(Cache)

# TODO: make a CacheBase with .state property
# TODO: should operators with .state check for len(args) on new emits?
