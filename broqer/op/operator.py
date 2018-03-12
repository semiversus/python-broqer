from broqer.stream import Stream, StreamDisposable
from typing import List
import asyncio

def build_stream_operator(operator_cls):
  def _op(*args, **kwargs):
    def _build(source_stream):
      return operator_cls(source_stream, *args, **kwargs)
    return _build
  return _op

class Operator(Stream):
  def __init__(self, *source_streams:List[Stream]):
    self._source_streams=source_streams
    Stream.__init__(self)

  def subscribe(self, stream:'Stream') -> StreamDisposable:
    if not self._subscriptions:
      for _stream in self._source_streams:
        _stream.subscribe(self)
    return Stream.subscribe(self, stream)
  
  def unsubscribe(self, stream:'Stream') -> None:
    Stream.unsubscribe(self, stream)
    if not self._subscriptions:
      for _stream in self._source_streams:
        _stream.unsubscribe(self)

  def unsubscribe_all(self) -> None:
    Stream.unsubscribe_all(self)
    for _stream in self._source_streams:
        _stream.unsubscribe(self)