from typing import Any

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._build_operator import build_operator


class Cache(Publisher, Subscriber):
  def __init__(self, publisher:Publisher, *start_values:Any, meta=None):
    Publisher.__init__(self, meta=meta)
    publisher.subscribe(self)
    self._cache=start_values

  def subscribe(self, subscriber:'Subscriber') -> SubscriptionDisposable:
    print('cache: ', self._cache)
    subscriber.emit(*self._cache, who=self)
    return super().subscribe(subscriber)

  def emit(self, *args:Any, who:Publisher) -> None:
    print('emit', args)
    for subscription in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscription.emit(*args, who=self)

    self._cache=args
  
  @property
  def value(self):
    return self._cache

cache=build_operator(Cache)