from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator

class Distinct(Operator):
  def emit(self, *args:Any, who:Publisher) -> None:
    assert len(args)>=1, 'need at least one argument for distinct'
    if args!=getattr(self, '_cache', None):
      self._cache=args
      self._emit(*args)
  
  @property
  def cache(self):
    cache=getattr(self, '_cache', (None,))
    if len(cache)==1:
      return cache[0]
    else:
      return cache

distinct=build_operator(Distinct)