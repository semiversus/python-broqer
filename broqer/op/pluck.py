from typing import Any, Callable
from operator import getitem

from broqer import Publisher

from ._operator import Operator, build_operator


class Pluck(Operator):
  def __init__(self, publisher:Publisher, *picks:Any):
    assert len(picks)>=1, 'need at least one pick key'
    Operator.__init__(self, publisher)

    self._picks=picks

  def emit(self, arg:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    for pick in self._picks:
      arg=getitem(arg, pick)
    self._emit(arg)


pluck=build_operator(Pluck)