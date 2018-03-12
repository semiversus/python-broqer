from broqer.stream import Stream
from typing import Any, List
from .operator import build_stream_operator, Operator

class CombineLatest(Operator):
  def __init__(self, *source_streams:List[Stream]):
    Operator.__init__(self, *source_streams)
    self._last_msg=[None for _ in source_streams]
    self._missing=set(source_streams)
    # TODO: additional keyword to decide if emit undefined values
  
  def emit(self, *args:Any, who:Stream):
    if self._missing and who in self._missing:
      self._missing.remove(who)
    self._last_msg[self._source_streams.index(who)]=args
    if not self._missing:
      self._emit(*self._last_msg)

combine_latest=build_stream_operator(CombineLatest)