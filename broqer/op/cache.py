from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Cache(Operator):
  def __init__(self, publisher:Publisher, *start_values:Any):
    Operator.__init__(self, publisher)
    assert len(start_values)>=1, 'need at least one argument for cache start_values'
    self._cache=start_values

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=super().subscribe(subscriber)
    subscriber.emit(*self._cache, who=self)
    return disposable

  def emit(self, *args:Any, who:Publisher) -> None:
    self._cache=args
    self._emit(*args)
  
  @property
  def cache(self):
    if len(self._cache)==1:
      return self._cache[0]
    else:
      return self._cache

cache=build_operator(Cache)

#TODO: make a CacheBase with .cache property