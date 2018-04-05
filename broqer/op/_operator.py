import asyncio
from typing import Any, List

from broqer.base import Publisher, Subscriber, SubscriptionDisposable


class Operator(Publisher, Subscriber):
  def __init__(self, *publishers:List[Publisher]):
    super().__init__()
    self._publishers=publishers

  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    if not self._subscriptions:
      for _publisher in self._publishers:
        _publisher.subscribe(self)
    return Publisher.subscribe(self, subscriber)
  
  def unsubscribe(self, subscriber:'Subscriber') -> None:
    Publisher.unsubscribe(self, subscriber)
    if not self._subscriptions:
      for _publisher in self._publishers:
        _publisher.unsubscribe(self)
  
  def _emit(self, *args:Any) -> None:
    if self._cache is not None:
      self._cache=args
    for subscriber in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscriber.emit(*args, who=self)
