from typing import Any, Callable, Optional, Union
from types import MappingProxyType

from broqer import Subscriber, SubscriptionDisposable

class Publisher():
  def __init__(self):
    self._subscriptions=set()
   
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
  
  def __or__(self, sink:Union['Subscriber', Callable[['Publisher'], 'Publisher']]) -> 'Publisher':
    if isinstance(sink, Subscriber):
      return self.subscribe(sink)
    else:
      return sink(self)

  def __await__(self):
    from broqer.op import ToFuture
    return ToFuture(self).__await__()