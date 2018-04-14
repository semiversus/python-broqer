from typing import Any, Optional

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator

class Distinct(Operator):
  def __init__(self, publisher:Publisher, *start_values:Any):
    Operator.__init__(self, publisher)
    if not start_values:
      self._cache=None
    else:
      self._cache=start_values

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    cache=self._cache # replace self._cache temporary with None
    self._cache=None
    disposable=super().subscribe(subscriber)
    if self._cache is None and cache is not None: # if subscriber was not emitting on subscription
      self._cache=cache # set self._cache back
      subscriber.emit(*self._cache, who=self) # and emit actual cache
    return disposable

  def emit(self, *args:Any, who:Publisher) -> None:
    assert len(args)>=1, 'need at least one argument for distinct'
    if args!=self._cache:
      self._cache=args
      self._emit(*args)
  
  @property
  def cache(self):
    if self._cache is None:
      return None
    if len(self._cache)==1:
      return self._cache[0]
    else:
      return self._cache

distinct=build_operator(Distinct)