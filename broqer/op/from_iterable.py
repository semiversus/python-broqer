from typing import Any, List

from broqer import Publisher, Subscriber, SubscriptionDisposable


class FromIterable(Publisher):
  def __init__(self, iterable):
    super().__init__()
    self._iterable=iterable

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=Publisher.subscribe(self, subscriber)
    for v in self._iterable:
      self._emit(v)
    return disposable