from broqer.stream import Stream
from typing import Callable, Any
from .operator import build_stream_operator

class Sink(Stream):
  def __init__(self, source_stream:Stream, sink_function:Callable[[Any], None]):
    Stream.__init__(self)
    self._sink_function=sink_function
    self._disposable=source_stream.subscribe(self)
  
  def emit(self, *args:Any, who:Stream):
    self._sink_function(*args)
    self._emit(*args)
  
  def dispose(self):
    self._disposable.dispose()

sink=build_stream_operator(Sink)