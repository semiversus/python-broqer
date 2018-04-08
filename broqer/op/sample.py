import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable

from ._build_operator import build_operator


class Sample(Publisher, Subscriber, Disposable):
  def __init__(self, publisher:Publisher, interval:float, meta=None):
    assert interval>0, 'interval has to be positive'

    Publisher.__init__(self, meta=meta)

    self._interval=interval
    self._call_later_handle=None
    self._loop=asyncio.get_event_loop()

    self._disposable=publisher.subscribe(self)

  def _periodic_callback(self):
    for subscription in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscription.emit(*self._cache, who=self)

    if self._subscriptions:
      self._call_later_handle=self._loop.call_later(self._interval, self._periodic_callback)

  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
    self._cache=args

    if self._call_later_handle is None:
      self._periodic_callback()
  
  def dispose(self):
    self._disposable.dispose()

sample=build_operator(Sample)