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
    self._meta_dict.update(meta_dict)
  
  @classmethod
  def register_operator(cls, operator_cls, name):
    def _(source_stream, *args, **kwargs):
      return operator_cls(source_stream, *args, **kwargs)
    setattr(cls, name, _)

import broqer._operators