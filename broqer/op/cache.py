"""
Caching the emitted values to access it via ``.cache`` property.

The ``Cache`` publisher is emitting a value on subscription.

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> cached_publisher = s | op.cache(0)
>>> _disposable = cached_publisher | op.sink(print, sep=' - ')
0

>>> s.emit(3)
3
>>> cached_publisher.cache
3

Also working with multiple arguments in emit:

>>> s.emit(1, 2)
1 - 2
>>> cached_publisher.cache
(1, 2)
"""

from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Cache(Operator):
    def __init__(self, publisher: Publisher, *init: Any) -> None:
        Operator.__init__(self, publisher)
        assert len(init) >= 1, 'need at least one argument for cache init'
        self._cache = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        cache = self._cache  # replace self._cache temporary with None
        self._cache = None
        disposable = super().subscribe(subscriber)
        if self._cache is None:
            # if subscriber was not emitting on subscription
            self._cache = cache  # set self._cache back
            subscriber.emit(*self._cache, who=self)  # and emit actual cache
        return disposable

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._cache = args
        self._emit(*args)

    @property
    def cache(self):
        if len(self._cache) == 1:
            return self._cache[0]
        else:
            return self._cache


cache = build_operator(Cache)

# TODO: make a CacheBase with .cache property
# TODO: should operators with .cache check for len(args) on new emits?
