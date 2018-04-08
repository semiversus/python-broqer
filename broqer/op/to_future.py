import asyncio
from typing import Any, Optional

from broqer import Subscriber

from ._build_operator import build_operator

class ToFuture(Subscriber):
  def __init__(self, publisher, timeout=None, loop=None):
    self._disposable=publisher.subscribe(self)

    if loop is None:
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

  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
    if len(args)==1:
      self._future.set_result(args[0])
    else:
      self._future.set_result(args)
 
to_future=build_operator(ToFuture)
