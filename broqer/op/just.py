"""
Emit a (constant) value on subscribe.

Usage:

>>> from broqer import op
>>> j = op.Just(1)

>>> _d1 = j | op.sink(print, 'Dump1:')
Dump1: 1

>>> _d2 = j | op.sink(print, 'Dump2:')
Dump2: 1

"""
from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Just(Publisher):
    def __init__(self, value: Any) -> None:
        Publisher.__init__(self)
        self._state = value

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        subscriber.emit(self._state, who=self)
        return disposable

    def get(self):
        return self._state
