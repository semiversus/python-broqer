from typing import Any, Callable, Optional, Union

from broqer.base import Subscriber, SubscriptionDisposable

class Publisher():
  def __init__(self):
    self._subscriptions=set()
    self._cache=None
    
  def setup(self, *cache:Any, meta:Optional[dict]=None) -> 'Publisher':
    self._cache=cache
    self._meta=meta
    return self

  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    self._subscriptions.add(subscriber)
    if self._cache is not None:
      subscriber.emit(*self._cache, who=self)
    return SubscriptionDisposable(self, subscriber)

  def unsubscribe(self, subscriber:'Subscriber') -> None:
    self._subscriptions.remove(subscriber)

  @property
  def cache(self):
    return self._cache

  @property
  def meta(self):
    return getattr(self, '_meta', None)
  
  @meta.setter
  def meta(self, meta_dict:dict):
    if hasattr(self, '_meta'):
      raise ValueError('Publisher setup already done')
    self._meta=meta_dict
  
  @classmethod
  def register_operator(cls, operator_cls, name):
    def op(source_stream, *args, **kwargs):
      return operator_cls(source_stream, *args, **kwargs)
    setattr(cls, name, op)
  
  def __or__(self, sink:Union['Subscriber', Callable[['Publisher'], 'Publisher']]) -> 'Publisher':
    if isinstance(sink, Subscriber):
      return self.subscribe(sink)
    else:
      return sink(self)
  
  def __await__(self):
    from broqer.op.to_future import ToFuture
    return ToFuture(self).__await__()
