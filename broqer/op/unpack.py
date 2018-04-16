from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Unpack(Operator):
  def emit(self, arg:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    self._emit(*arg)


unpack=build_operator(Unpack)
