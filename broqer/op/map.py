from .operator import build_stream_operator, Operator
from broqer.stream import Stream
from typing import Any, Callable

class Map(Operator):
  def __init__(self, source_stream:Stream, map_func:Callable[[Any], Any]):
    Operator.__init__(self, source_stream)
    self._map_func=map_func

  def emit(self, *args:Any, who:Stream):
    arg, *args,=self._map_func(*args), None
    self._emit(arg, *args[:-1])

map=build_stream_operator(Map)