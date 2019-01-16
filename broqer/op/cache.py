"""
>>> from broqer import Subject, op
>>> s = Subject()

>>> cached_publisher = s | op.Cache(0)
>>> _disposable = cached_publisher | op.Sink(print, sep=' - ')
0

>>> s.emit(3)
3
"""
import asyncio
from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable, NONE

from .operator import Operator


class Cache(Operator):
    """ Caching the emitted values (make a stateless publisher stateful)

    The ``Cache`` publisher is emitting a value on subscription.

    :param init: initialization for state
    """
    def __init__(self, init: Any = NONE) -> None:
        Operator.__init__(self)
        self._state = init

    def subscribe(self, subscriber: Subscriber,
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        old_state = self._state  # to check if .emit was called

        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._publisher.subscribe(self._emit_sink)

        try:
            value = self._publisher.get()
        except ValueError:
            if self._state is not NONE:
                subscriber.emit(self._state, who=self)
        else:
            if len(self._subscriptions) > 1 or old_state == self._state:
                subscriber.emit(value, who=self)

        return disposable

    def get(self):
        try:
            return self._publisher.get()  # may raise ValueError
        except ValueError:
            if self._state is not NONE:
                return self._state
        Publisher.get(self)  # raises ValueError

    def emit_op(self, value: Any, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        if self._state != value:
            self._state = value
            return self.notify(value)
        return None
