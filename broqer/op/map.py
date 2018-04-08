from typing import Any, Callable, Optional

from broqer import Publisher

from ._build_operator import build_operator
from ._operator import Operator


class Map(Operator):
  def __init__(self, publisher:Publisher, map_func:Callable[[Any], Any]):
    """ special care for return values:
        * return `None` (or nothing) if you don't want to return a result
        * return `None,` if you want to return `None`
        * return `(a,b),` to return a tuple as value
        * every other return value will be unpacked
    """
 
    Operator.__init__(self, publisher)

    self._map_func=map_func

  def emit(self, *args:Any, who:Publisher) -> None:
    *args,_=self._map_func(*args),None
    try:
        *args,=args[0]
    except TypeError:
        if args[0] is None:
            args=()
    self._emit(*args)

map=build_operator(Map)