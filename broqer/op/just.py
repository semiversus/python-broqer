"""
Emit a (constant) value on subscribe.

Usage:
>>> from broqer import op
>>> j = op.Just(1)

>>> _d1 = j | op.sink(print, 'Dump1:')
Dump1: 1

>>> _d2 = j | op.sink(print, 'Dump2:')
Dump2: 1

>>> j.cache
1

Also handling zero or more than one argument:
>>> op.Just(1, 2).cache
(1, 2)
>>> i = op.Just()
>>> i.cache
>>> _d3 = i | op.sink(print, 'Dump Empty:')
Dump Empty:
"""
from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Just(Publisher):
    def __init__(self, *value: Any) -> None:
        super().__init__()
        self._cache = value

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        subscriber.emit(*self._cache, who=self)
        return disposable

    @property
    def cache(self):
        if len(self._cache) == 1:
            return self._cache[0]
        elif len(self._cache) == 0:
            return None
        else:
            return self._cache
