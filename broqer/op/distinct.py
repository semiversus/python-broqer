from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator

class Distinct(Operator):
  def emit(self, *args:Any, who:Publisher) -> None:
    if args!=getattr(self, '_cache', None):
      self._cache=args
      self._emit(*args)
  
  @property
  def cache(self):
    return self._cache

distinct=build_operator(Distinct)