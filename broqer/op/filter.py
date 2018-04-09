from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Filter(Operator):
  def __init__(self, publisher:Publisher, predicate:Callable[[Any], bool]):
 
    Operator.__init__(self, publisher)

    self._predicate=predicate

  def emit(self, *args:Any, who:Publisher) -> None:
    if self._predicate(*args):
      self._emit(*args)

filter=build_operator(Filter)