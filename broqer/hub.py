from collections import defaultdict
from typing import Any, Optional

from broqer import Publisher, Subscriber, SubscriptionDisposable


class ProxySubject(Publisher, Subscriber):
  def __init__(self):
    Publisher.__init__(self)
    self._subject=None

  def emit(self, *args:Any) -> None:
    # method will be replaced by .__call__
    raise TypeError('No subject is assigned to this ProxySubject')
  
  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    if self._subject:
      return self._subject.subscribe(subscriber)
    else:
      return super().subscribe(subscriber)
  
  def unsubscribe(self, subscriber:'Subscriber') -> None:
    if self._subject:
      self._subject.unsubscribe(subscriber)
    else:
      super().unsubscribe(subscriber)

  def __call__(self, publisher:Publisher) -> 'ProxySubject':
    # used for pipeline style assignment 
    if self._subject is not None:
      raise ValueError('ProxySubject is already assigned')
    self._subject=publisher
    if isinstance(self._subject, Subscriber):
      self.emit=self._subject.emit
    for subscriber in self._subscriptions:
      self._subject.subscribe(subscriber)
    self._subscriptions.clear()
    return self
  
  @property
  def assigned(self):
    return self._subject is not None
  
  @property
  def meta(self):
    return getattr(self, '_meta', None)
  
  @meta.setter
  def meta(self, meta_dict):
    if hasattr(self, '_meta'):
      raise ValueError('ProxySubject already has a meta dict')
    self._meta=meta_dict
  
 
class Hub:
  def __init__(self):
    self._proxies=defaultdict(ProxySubject)
  
  def __getitem__(self, path:str) -> ProxySubject:
    return self._proxies[path]
  
  def publish(self, path:str, meta:dict) -> ProxySubject:
    self[path].meta=meta
    return self[path]


class SubordinateHub:
  def __init__(self, hub, prefix):
    self._hub=hub
    self._prefix=prefix
  
  def __getitem__(self, path:str) -> ProxySubject:
    return self._proxies[self._prefix+path]
  
  def publish(self, path:str, meta:dict) -> ProxySubject:
    return self._hub.publish(self._prefix+path, meta)
  
  def resolve(self, path:str) -> str:
    return self._prefix+path
