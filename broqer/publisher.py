from typing import Any, Callable, Optional, Union
from types import MappingProxyType

from broqer import Subscriber, SubscriptionDisposable

class Publisher():
  def __init__(self, meta:Optional[dict]=None):
    self._subscriptions=set()
    if meta is not None:
      self._meta=MappingProxyType(meta)

  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    if subscriber in self._subscriptions:
      raise ValueError('Subscriber already registred')

    self._subscriptions.add(subscriber)
    return SubscriptionDisposable(self, subscriber)

  def unsubscribe(self, subscriber:'Subscriber') -> None:
    try:
      self._subscriptions.remove(subscriber)
    except KeyError:
      raise ValueError('Subscriber is not registred (anymore)')
  
  def __len__(self):
    """ number of subscriptions """
    return len(self._subscriptions)

  @property
  def meta(self):
    return getattr(self, '_meta', None)
  
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