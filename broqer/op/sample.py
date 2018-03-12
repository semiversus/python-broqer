from broqer.stream import Stream, StreamDisposable
from typing import Any
from .operator import Operator, build_stream_operator
import asyncio

class Sample(Operator):
  def __init__(self, source_stream:Stream, interval:float):
    assert interval>0, 'interval has to be positive'
    Operator.__init__(self, source_stream)
    self._interval=interval
    self._last_msg=None
    self._call_later_handle=None
    self._loop=asyncio.get_event_loop()
  
  def subscribe(self, stream:Stream) -> StreamDisposable:
    is_first=not self._subscriptions

    Operator.subscribe(self, stream)

    if is_first:
      self._periodic_callback()

  def unsubscribe(self, stream:Stream) -> None:
    Operator.unsubscribe(stream)
    if not self._subscriptions:
      self._last_msg=None
      if self._call_later_handle is not None:
        self._call_later_handle.cancel()
        self._call_later_handle=None

  def _periodic_callback(self):
    if self._last_msg is not None:
      self._emit(*self._last_msg)
    if self._subscriptions:
      self._call_later_handle=self._loop.call_later(self._interval, self._periodic_callback)
    else:
      assert self._call_later_handle is None, 'As no subscription is available _call_later_handle has to be None'

  def emit(self, *args:Any, who:Stream):
    self._last_msg=args

sample=build_stream_operator(Sample)