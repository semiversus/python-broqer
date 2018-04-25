"""
Only emit values which changed regarding to the cached state.

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> distinct_publisher = s | op.distinct()
>>> _disposable = distinct_publisher | op.sink(print)

>>> s.emit(1)
1
>>> s.emit(2)
2
>>> s.emit(2)
>>> distinct_publisher.cache
2
>>> _disposable.dispose()

Also working with multiple arguments in emit:

>>> distinct_publisher = s | op.distinct(0, 0)
>>> distinct_publisher | op.sink(print)
0 0
<...>
>>> s.emit(0, 0)
>>> s.emit(0, 1)
0 1
>>> distinct_publisher.cache
(0, 1)
"""

from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Distinct(Operator):
    def __init__(self, publisher: Publisher, *init: Any) -> None:
        Operator.__init__(self, publisher)
        if not init:
            self._cache = None
        else:
            self._cache = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        cache = self._cache  # replace self._cache temporary with None
        self._cache = None
        disposable = super().subscribe(subscriber)
        if self._cache is None and cache is not None:
            # if subscriber was not emitting on subscription
            self._cache = cache  # set self._cache back
            subscriber.emit(*self._cache, who=self)  # and emit actual cache
        return disposable

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        assert len(args) >= 1, 'need at least one argument for distinct'
        if args != self._cache:
            self._cache = args
            self._emit(*args)

    @property
    def cache(self):
        if self._cache is None:
            return None
        if len(self._cache) == 1:
            return self._cache[0]
        else:
            return self._cache


distinct = build_operator(Distinct)
