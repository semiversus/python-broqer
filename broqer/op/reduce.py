from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Reduce(Operator):
  def __init__(self, publisher:Publisher, func:Callable[[Any], Any], initializer=None):
    Operator.__init__(self, publisher)
    self._cache=initializer

    self._reduce_func=func

  def emit(self, arg:Any, who:Publisher) -> None:
    if self._cache is not None:
      self._cache=self._reduce_func(self._cache, arg)
      self._emit(self._cache)
    else:
      self._cache=arg

reduce=build_operator(Reduce)