from broqer.disposable import Disposable
from typing import Callable, Any, Optional, List
from types import MappingProxyType

class StreamDisposable(Disposable):
  def __init__(self, source_stream: 'Stream', sink_stream:'Stream') -> None:
    self._source_stream=source_stream
    self._sink_stream=sink_stream

  def dispose(self) -> None:
    self._source_stream.unsubscribe(self._sink_stream)

class Stream:
  def __init__(self):
    self._subscriptions=set()
    self._meta_dict=dict()

  def subscribe(self, stream:'Stream') -> StreamDisposable:
    self._subscriptions.add(stream)
    return StreamDisposable(self, stream)

  def unsubscribe(self, stream:'Stream') -> None:
    self._subscriptions.remove(stream)
  
  def unsubscribe_all(self) -> None:
    self._subscriptions.clear()

  def _emit(self, msg_data:Any) -> None:
    for stream in self._subscriptions:
      # TODO: critical place to think about handling exceptions
      stream.emit(msg_data, self)

  def emit(self, msg_data:Any, who:Optional['Stream']=None) -> None:
      self._emit(msg_data)
 
  @property
  def meta(self):
    return MappingProxyType(self._meta_dict)
  
  @meta.setter
  def meta(self, meta_dict:dict):
    assert not self._meta_dict, 'Meta dict already set'
    self._meta_dict.udate(meta_dict)
  
  @classmethod
  def register_operator(cls, operator_cls, name):
    def _(source_stream, *args, **kwargs):
      return operator_cls(source_stream, *args, **kwargs)
    setattr(cls, name, _)

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

class Map(Operator):
  def __init__(self, source_stream, map_func):
    Operator.__init__(self, source_stream)
    self._map_func=map_func

  def emit(self, msg_data:Any, who:Stream):
    self._emit(self._map_func(msg_data))

Stream.register_operator(Map, 'map')

class Sink(Stream):
  def __init__(self, source_stream, sink_function):
    Stream.__init__(self)
    self._sink_function=sink_function
    self._disposable=source_stream.subscribe(self)
  
  def emit(self, msg_data:Any, who:Stream):
    self._sink_function(msg_data)
    self._emit(msg_data)
  
  def dispose(self):
    self._disposable.dispose()

Stream.register_operator(Sink, 'sink')