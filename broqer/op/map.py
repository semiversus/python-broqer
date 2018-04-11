from functools import partial
from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Map(Operator):
  def __init__(self, publisher:Publisher, map_func:Callable[[Any], Any], *args, **kwargs):
    """ special care for return values:
        * return `None` (or nothing) if you don't want to return a result
        * return `None,` if you want to return `None`
        * return `(a,b),` to return a tuple as value
        * every other return value will be unpacked
    """
 
    Operator.__init__(self, publisher)

    if args or kwargs:
      self._map_func=partial(map_func, *args, **kwargs)
    else:
      self._map_func=map_func

  def emit(self, *args:Any, who:Publisher) -> None:
    result=self._map_func(*args)
    if result is None:
      result=()
    elif not isinstance(result, tuple):
      result=(result,)
    self._emit(*result)

map=build_operator(Map)
