from typing import Any, Optional

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator

class Distinct(Operator):
  def __init__(self, publisher:Publisher, *start_values:Optional[Any]=None):
    Operator.__init__(self, publisher)
    self._cache=start_values

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=super().subscribe(subscriber)
    if self._cache is not None:
      subscriber.emit(*self._cache, who=self)
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