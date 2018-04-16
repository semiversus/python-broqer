from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class CatchException(Operator):
  def __init__(self, publisher:Publisher, *exceptions):
    Operator.__init__(self, publisher)
    self._exceptions=exceptions

  def emit(self, *args:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    try:
      self._emit(*args)
    except self._exceptions:
      pass


catch_exception=build_operator(CatchException)
