import asyncio
from typing import Any, List

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Operator(Publisher, Subscriber):
  def __init__(self, *publishers:List[Publisher]):
    super().__init__()
    self._publishers=publishers

  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    disposable=Publisher.subscribe(self, subscriber)
    if len(self._subscriptions)==1: # if this was the first subscription
      for _publisher in self._publishers: # subscribe to all dependent publishers
        _publisher.subscribe(self)
    return disposable
  
  def unsubscribe(self, subscriber:'Subscriber') -> None:
    Publisher.unsubscribe(self, subscriber)
    if not self._subscriptions:
      for _publisher in self._publishers:
        _publisher.unsubscribe(self)
  
  def _emit(self, *args:Any) -> None:
    for subscriber in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscriber.emit(*args, who=self)

def build_operator(operator_cls):
  def _op(*args, **kwargs):
    def _build(publisher):
      return operator_cls(publisher, *args, **kwargs)
    return _build
  return _op