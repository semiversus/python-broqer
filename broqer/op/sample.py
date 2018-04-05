import asyncio
from typing import Any, Optional

from broqer.base import Publisher, Subscriber, SubscriptionDisposable

from ._build_operator import build_operator
from ._operator import Operator


class Sample(Operator):
  def __init__(self, publisher:Publisher, interval:float):
    assert interval>0, 'interval has to be positive'
    assert publisher._cache is not None, 'Sample can only be used with caching publishers'

    Operator.__init__(self, publisher)

    self._interval=interval
    self._cache=publisher._cache
    self._call_later_handle=None
    self._loop=asyncio.get_event_loop()
  
  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    is_first=not self._subscriptions

    disposable=Operator.subscribe(self, subscriber)

    if is_first:
      self._periodic_callback()
    
    return disposable

  def unsubscribe(self, subscriber:Subscriber) -> None:
    Operator.unsubscribe(subscriber)
    if not self._subscriptions:
      if self._call_later_handle is not None:
        self._call_later_handle.cancel()
        self._call_later_handle=None

  def _periodic_callback(self):
    for subscriber in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscriber.emit(*self._cache, who=self)

    if self._subscriptions:
      self._call_later_handle=self._loop.call_later(self._interval, self._periodic_callback)
    else:
      assert self._call_later_handle is None, 'As no subscription is available _call_later_handle has to be None'

  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
    self._cache=args

sample=build_operator(Sample)