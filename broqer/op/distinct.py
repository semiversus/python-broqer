from broqer.stream import Stream
from typing import Any
from .operator import build_stream_operator, Operator

class Distinct(Operator):
  def __init__(self, source_stream:Stream):
    Operator.__init__(self, source_stream)
    self._last_msg=None

  def emit(self, *args:Any, who:Stream):
    if args!=self._last_msg:
      self._last_msg=args
      self._emit(*args)

distinct=build_stream_operator