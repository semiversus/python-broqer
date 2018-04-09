from typing import Any, Callable
from operator import getitem

from broqer import Publisher

from ._operator import Operator, build_operator


class Pluck(Operator):
  def __init__(self, publisher:Publisher, pick:Any):
    Operator.__init__(self, publisher)

    self._pick=pick

  def emit(self, arg:Any, who:Publisher) -> None:
    self._emit(getitem(arg, self._pick))

pluck=build_operator(Pluck)