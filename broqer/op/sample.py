import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable

from ._build_operator import build_operator
from ._operator import Operator


class Sample(Operator, Disposable):
  def __init__(self, publisher:Publisher, interval:float):
    assert interval>0, 'interval has to be positive'

    Operator.__init__(self, publisher)

    self._interval=interval
    self._call_later_handle=None
    self._loop=asyncio.get_event_loop()
    print('sample:init')

  def _periodic_callback(self):
    print('sample:periodic', self._cache, len(self))
    for subscription in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscription.emit(*self._cache, who=self)

    if self._subscriptions:
      self._call_later_handle=self._loop.call_later(self._interval, self._periodic_callback)

  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
    print("sample:emit", args)
    self._cache=args

    if self._call_later_handle is None:
      self._periodic_callback()
  
  def dispose(self):
    self._disposable.dispose()

sample=build_operator(Sample)