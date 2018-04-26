from typing import Any, Optional

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Subject(Publisher, Subscriber):
    """
    Source with ``.emit(*args)`` method to publish a new message.

    >>> from broqer import op

    >>> s = Subject()
    >>> _d = s | op.sink(print)
    >>> s.emit(1)
    1
    """
    emit = Publisher._emit  # type: ignore


class Value(Publisher, Subscriber):
    """
    Source with a state (initialized via ``init``)

    >>> from broqer import op

    >>> s = Value(0)
    >>> _d = s | op.sink(print)
    0
    >>> s.emit(1)
    1
    >>> s.cache
    1
    >>> s.emit(1, 2)
    1 2
    >>> s.cache
    (1, 2)
    """
    def __init__(self, *init):
        super().__init__()
        self._cache = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = super().subscribe(subscriber)
        subscriber.emit(*self._cache, who=self)
        return disposable

    def emit(self, *args: Any, who: Optional[Publisher]=None) -> None:
        self._cache = args
        self._emit(*args)

    @property
    def cache(self):
        if len(self._cache) == 1:
            return self._cache[0]
        else:
            return self._cache
