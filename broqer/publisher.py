from typing import Any, Callable, Optional, Union
from types import MappingProxyType

from broqer import Subscriber, SubscriptionDisposable

class Publisher():
  def __init__(self):
    self._subscriptions=set()
   
  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    if subscriber in self._subscriptions:
      raise ValueError('Subscriber already registered')

    self._subscriptions.add(subscriber)
    return SubscriptionDisposable(self, subscriber)

  def unsubscribe(self, subscriber:'Subscriber') -> None:
    try:
      self._subscriptions.remove(subscriber)
    except KeyError:
      raise ValueError('Subscriber is not registered (anymore)')
  
  def _emit(self, *args:Any) -> None:
    """ emit to all subscriptions """
    for subscriber in tuple(self._subscriptions):
      subscriber.emit(*args, who=self)

  def __len__(self):
    """ number of subscriptions """
    return len(self._subscriptions)
  
  def __or__(self, build_subscriber:Callable[['Publisher'], 'Publisher']) -> 'Publisher':
    # build_subscriber is called with `self` and returns a new publisher
    return build_subscriber(self)

  def __await__(self):
    from broqer.op import ToFuture # lazy import due circular dependency
    return ToFuture(self).__await__()