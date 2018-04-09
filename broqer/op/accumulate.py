from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Accumulate(Operator):
  def __init__(self, publisher:Publisher, func:Callable[[Any], Any], initializer):
    Operator.__init__(self, publisher)
    self._acc_func=func
    self._state=initializer

  def reset(self, initializer):
    self._state=initializer
    
  def emit(self, arg:Any, who:Publisher) -> None:
    self._state, result=self._acc_func(self._state, arg)
    self._emit(result)

accumulate=build_operator(Accumulate)