from broqer.base import Disposable, Publisher, Subscriber
from typing import Callable, Any, Optional, List, Union
from types import MappingProxyType

class StreamDisposable(Disposable):
  def __init__(self, source_stream:'Stream', sink_stream:'Stream') -> None:
    self._source_stream=source_stream
    self._sink_stream=sink_stream

  def dispose(self) -> None:
    self._source_stream.unsubscribe(self._sink_stream)

class Stream(Publisher, Subscriber):
  def __init__(self):
    self._subscriptions=set()
    self._meta_dict=dict()
    self._retain=None

  def setup(self, *retain:Any, meta:Optional[dict]=None) -> 'Stream':
    if meta is not None:
      self.meta=meta
    
    if retain:
      self._retain=retain
    return self

  def subscribe(self, stream:'Stream') -> StreamDisposable:
    self._subscriptions.add(stream)
    if self._retain is not None:
      stream.emit(*self._retain, who=self)
    return StreamDisposable(self, stream)

  def unsubscribe(self, stream:'Stream') -> None:
    self._subscriptions.remove(stream)
  
  def unsubscribe_all(self) -> None:
    # why not simple clear subscriptions set? -> .unsubscribe could be overwritten
    # copy subscriptions set into a tuple, because subscription set will be changed while iterating over it
    for stream in tuple(self._subscriptions):
      self.unsubscribe(stream)

  def _emit(self, *args:Any) -> None:
    if self._retain is not None:
      self._retain=args
    for stream in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      stream.emit(*args, who=self)

  def emit(self, *args:Any, who:Optional['Stream']=None) -> None:
      self._emit(*args)
 
  @property
  def retain(self):
    return self._retain

  @property
  def meta(self):
    return MappingProxyType(self._meta_dict)
  
  @meta.setter
  def meta(self, meta_dict:dict):
    assert not self._meta_dict, 'Meta dict already set'
    self._meta_dict.update(meta_dict)
  
  def __await__(self):
    return AsFuture(self).__await__()
  
  @classmethod
  def register_operator(cls, operator_cls, name):
    def _(source_stream, *args, **kwargs):
      return operator_cls(source_stream, *args, **kwargs)
    setattr(cls, name, _)
  
  def __or__(self, sink:Union['Stream', Callable[['Stream'], 'Stream']]) -> 'Stream':
    if isinstance(sink, Stream):
      return self.subscribe(sink)
    else:
      return sink(self)

from broqer.op import AsFuture
Stream.register_operator(AsFuture, 'as_future')