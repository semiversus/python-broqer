import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable

from ._operator import Operator, build_operator


class Sample(Operator):
  def __init__(self, publisher:Publisher, interval:float):
    assert interval>0, 'interval has to be positive'

    Operator.__init__(self, publisher)

    self._interval=interval
    self._call_later_handle=None
    self._loop=asyncio.get_event_loop()

  def _periodic_callback(self):
    """ will be started on first emit """
    self._emit(*self._cache) # emit to all subscribers

    if self._subscriptions: # if there are still subscriptions register next _periodic callback
      self._call_later_handle=self._loop.call_later(self._interval, self._periodic_callback)
    else:
      self._call_later_handle=None

  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
    self._cache=args

    if self._call_later_handle is None:
      self._periodic_callback()

sample=build_operator(Sample)