from typing import Any, Optional

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Subject(Publisher, Subscriber):
    emit = Publisher._emit  # type: ignore


class Value(Publisher, Subscriber):
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
        return self._cache
