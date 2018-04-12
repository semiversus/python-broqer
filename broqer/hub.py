from broqer import Publisher, Subscriber, SubscriptionDisposable
from collections import defaultdict
from typing import Any, Optional

class ProxyPublisher(Publisher, Subscriber):
  def __init__(self):
    Publisher.__init__(self)
    self._publisher=None

  def emit(self, *args:Any) -> None:
    if self._publisher is None:
      raise TypeError('No publisher is assigned to this ProxyPublisher')
    self._publisher.emit(*args)
  
  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    if self._publisher:
      return self._publisher.subscribe(subscriber)
    else:
      return super().subscribe(subscriber)
  
  def unsubscribe(self, subscriber:'Subscriber') -> None:
    if self._publisher:
      self._publisher.unsubscribe(subscriber)
    else:
      super().unsubscribe(subscriber)

  def __call__(self, publisher:Publisher) -> 'ProxyPublisher':
    self.assign(publisher)
    return self

  def assign(self, publisher:Publisher) -> None:
    if self._publisher is not None:
      raise ValueError('ProxyPublisher is already assigned')
    self._publisher=publisher
    for subscriber in self._subscriptions:
      self._publisher.subscribe(subscriber)
    self._subscriptions.clear()
  
  @property
  def assigned(self):
    return self._publisher is not None
  
  @property
  def meta(self):
    return getattr(self, '_meta', None)
  
  @meta.setter
  def meta(self, meta_dict):
    if hasattr(self, '_meta'):
      raise ValueError('ProxyPublisher already has a meta dict')
    self._meta=meta_dict
  
 
class Hub:
  def __init__(self):
    self._proxies=defaultdict(ProxyPublisher)
  
  def __getitem__(self, path:str) -> ProxyPublisher:
    return self._proxies[path]
  
  def __setitem__(self, path:str, publisher:Publisher) -> None:
    self._proxies[path].assign(publisher)

class SubordinateHub:
  def __init__(self, hub, prefix):
    self._hub=hub
    self._prefix=prefix
  
  def __getitem__(self, path:str) -> ProxyPublisher:
    return self._proxies[self._prefix+path]