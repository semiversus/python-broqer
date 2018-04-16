from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Pack(Operator):
  def emit(self, *args:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    self._emit(args)


pack=build_operator(Pack)
