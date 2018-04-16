from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import MultiOperator, build_operator


class Merge(MultiOperator):
  def __init__(self, *publishers:Publisher):
    Operator.__init__(self, *publisher)

  def emit(self, *args:Any, who:Publisher) -> None:
    assert who in self._publishers, 'emit comming from non assigned publisher'
    self._emit(self._cache)


merge=build_operator(Merge)