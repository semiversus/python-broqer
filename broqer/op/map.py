from typing import Any, Callable, Optional

from broqer.base import Publisher

from ._build_operator import build_operator
from ._operator import Operator


class Map(Operator):
  def __init__(self, publisher:Publisher, map_func:Callable[[Any], Any]):
    Operator.__init__(self, publisher)

    self._map_func=map_func

    if publisher._cache is not None:
      self._cache=self._map_func(*publisher._cache)

  def emit(self, *args:Any, who:Publisher) -> None:
    arg, *args,=self._map_func(*args), None
    self._emit(arg, *args[:-1])

map=build_operator(Map)