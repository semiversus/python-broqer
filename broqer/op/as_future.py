from broqer.stream import Stream
from typing import Any
from .operator import build_stream_operator, Operator
import asyncio

class AsFuture(Stream):
  def __init__(self, source_stream, timeout=None):
    Stream.__init__(self)
    self._disposable=source_stream.subscribe(self)

    loop=asyncio.get_event_loop()
    self._future=loop.create_future()
    self._future.add_done_callback(self._future_done)
    
    if timeout is not None:
      self._timeout_handle=loop.call_later(timeout, self._timeout)
    else:
      self._timeout_handle=None
      
  def _timeout(self):
    self._future.set_exception(asyncio.TimeoutError)
  
  def _future_done(self, future):
    self._disposable.dispose()
    if self._timeout_handle is not None:
      self._timeout_handle.cancel()

  def __await__(self):
    return self._future.__await__()

  def emit(self, *args:Any, who:Stream):
    if len(args)==1:
      self._future.set_result(args[0])
    else:
      self._future.set_result(args)
 
as_future=build_stream_operator(AsFuture)