from broqer.stream import Stream
from typing import Any
from .operator import build_stream_operator, Operator
import asyncio

class MapAsync(Operator):
  def __init__(self, source_stream, async_func):
    # TODO: supporting various modes when coroutine is running while next value is emitted
    # concurrent - just run coroutines concurrent
    # replace - cancel running and call for new value
    # queue - queue the value(s) and call after coroutine is finished
    # last - use last emitted value after coroutine is finished
    # skip - skip values emitted during coroutine is running
    Operator.__init__(self, source_stream)
    self._async_func=async_func
    self._future=None
  
  def emit(self, *args:Any, who:Stream):
    self._future=asyncio.ensure_future(self._async_func(*args))
    self._future.add_done_callback(self._future_done)
  
  def _future_done(self, future):
    if future.done():
      arg, *args=future.result(), None
      self._emit(arg, *args[:-1])
    else:
      #TODO how to handle an exception?
      pass

map_async=build_stream_operator(MapAsync)