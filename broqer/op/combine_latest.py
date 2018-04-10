from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import MultiOperator, build_operator


class CombineLatest(MultiOperator):
  def __init__(self, *publishers:Publisher):
    Operator.__init__(self, *publisher)
    self._cache=[None for _ in publishers]
    self._missing=set(publishers)
    self._index={p:i for i,p in enumerate(publishers)}
    
  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=Operator.subscribe(self, subscriber)
    if not self._missing:
      subscriber.emit(*self._cache, who=self)
    return disposable

  def emit(self, *args:Any, who:Publisher) -> None:
    if self._missing and who in self._missing:
      self._missing.remove(who)
    if len(args)==1:
      args=args[0]
    self._cache[self._index[who]]=args
    if not self._missing:
      self._emit(self._cache)
  
  @property
  def cache(self):
    return self._cache

combine_latest=build_operator(CombineLatest)