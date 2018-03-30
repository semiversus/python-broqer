from broqer.stream import Stream
from typing import Callable, Any, Optional
from .operator import build_stream_operator
from broqer.base import Disposable

class Sink(Stream, Disposable):
  def __init__(self, source_stream:Stream, sink_function:Callable[[Any], None]):
    Stream.__init__(self)
    self._sink_function=sink_function
    self._disposable=source_stream.subscribe(self)
  
  def emit(self, *args:Any, who:Optional[Stream]=None):
    self._sink_function(*args)
  
  def dispose(self):
    self._disposable.dispose()

sink=build_stream_operator(Sink)