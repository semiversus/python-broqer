from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class CombineLatest(Operator):
  def __init__(self, *publishers:Publisher):
    Operator.__init__(self, *publisher)
    self._cache=[None for _ in publishers]
    self._missing=set(publishers)
    
  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=Operator.subscribe(self, subscriber)
    if not self._missing:
      subscriber.emit(*self._cache, who=self)
    return disposable

  def emit(self, *args:Any, who:Publisher) -> None:
    if self._missing and who in self._missing:
      self._missing.remove(who)
    self._cache[self._publishers.index(who)]=args
    if not self._missing:
      self._emit(*self._cache)
  
  @property
  def cache(self):
    return self._cache

combine_latest=build_operator(CombineLatest)