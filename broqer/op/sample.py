import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable, SubscriptionDisposable

from ._operator import Operator, build_operator


class Sample(Operator):
  def __init__(self, publisher:Publisher, interval:float, loop=None):
    assert interval>0, 'interval has to be positive'

    Operator.__init__(self, publisher)

    self._interval=interval
    self._call_later_handle=None
    self._loop=loop or asyncio.get_event_loop()
    self._cache=None

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=super().subscribe(subscriber)
    if self._cache is not None:
      subscriber.emit(*self._cache, who=self)
    return disposable

  def _periodic_callback(self):
    """ will be started on first emit """
    self._emit(*self._cache) # emit to all subscribers

    if self._subscriptions: # if there are still subscriptions register next _periodic callback
      self._call_later_handle=self._loop.call_later(self._interval, self._periodic_callback)
    else:
      self._cache=None
      self._call_later_handle=None

  def emit(self, *args:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    self._cache=args

    if self._call_later_handle is None:
      self._periodic_callback()
  
  @property
  def cache(self):
    if self._cache is None:
      return None
    if len(self._cache)==1:
      return self._cache[0]
    else:
      return self._cache


sample=build_operator(Sample)