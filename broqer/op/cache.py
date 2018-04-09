from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Cache(Operator):
  def __init__(self, publisher:Publisher, *start_values:Any):
    Operator.__init__(self, publisher)
    self._cache=start_values

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=Operator.subscribe(self, subscriber)
    subscriber.emit(*self._cache, who=self)
    return disposable

  def emit(self, *args:Any, who:Publisher) -> None:
    self._cache=args
    self._emit(*args)
  
  @property
  def cache(self):
    return self._cache

cache=build_operator(Cache)