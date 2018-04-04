from broqer.base import Disposable, Publisher, Subscriber
from typing import Callable, Any, Optional, List, Union

class SubscriptionDisposable(Disposable):
  def __init__(self, publisher:'Publisher', subscriber:'Subscriber') -> None:
    self._publisher=publisher
    self._subscriber=subscriber

  def dispose(self) -> None:
    self._publisher.unsubscribe(self._subscriber)

class Stream(Publisher, Subscriber):
  def __init__(self):
    self._subscriptions=set()
    self._meta_dict=dict()
    self._cache=None

  ### publisher functionality
  
  def setup(self, *cache:Any, meta:Optional[dict]=None) -> 'Publisher':
    if meta is not None:
      self.meta=meta
    
    if cache:
      self._cache=cache
    return self

  def subscribe(self, stream:'Subscriber') -> StreamDisposable:
    self._subscriptions.add(stream)
    if self._cache is not None:
      stream.emit(*self._cache, who=self)
    return StreamDisposable(self, stream)

  def unsubscribe(self, stream:'Subscriber') -> None:
    self._subscriptions.remove(stream)
  
  @property
  def cache(self):
    return self._cache

  @property
  def meta(self):
    return MappingProxyType(self._meta_dict)
  
  @meta.setter
  def meta(self, meta_dict:dict):
    assert not self._meta_dict, 'Meta dict already set'
    self._meta_dict.update(meta_dict)

  ### subscribe functionality

  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
      self._emit(*args)
  
  def _emit(self, *args:Any) -> None:
    if self._cache is not None:
      self._cache=args
    for stream in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      stream.emit(*args, who=self)

  def __await__(self):
    return AsFuture(self).__await__()

from broqer.op import AsFuture
Stream.register_operator(AsFuture, 'as_future')