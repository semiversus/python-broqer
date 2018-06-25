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
    def __init__(self):
        Publisher.__init__(self)
        Subscriber.__init__(self)

    emit = Publisher.notify  # type: ignore


class Value(Publisher, Subscriber):
    """
    Source with a state (initialized via ``init``)

    >>> from broqer import op

    >>> s = Value(0)
    >>> _d = s | op.sink(print)
    0
    >>> s.emit(1)
    1
    >>> s.emit(1, 2)
    1 2
    """
    def __init__(self, *init):
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._state = init

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        subscriber.emit(*self._state, who=self)
        return disposable

    def emit(self, *args: Any, who: Optional[Publisher]=None) -> None:
        self._state = args
        self.notify(*args)
