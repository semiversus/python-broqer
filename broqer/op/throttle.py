import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable

from ._operator import Operator, build_operator


class Throttle(Operator):
  def __init__(self, publisher:Publisher, duration:float, loop=None):
    assert duration>=0, 'duration has to be positive'

    Operator.__init__(self, publisher)

    self._duration=duration
    self._loop=loop or asyncio.get_event_loop()
    self._wait_future=None
    self._cache=None

  def emit(self, *args:Any, who:Publisher) -> None:
    self._cache=args
    if self._wait_future is None or self._wait_future.done():
      self._wait_future=asyncio.sleep(self._duration)
      self._wait_future.add_done_callback(self._wait_done_cb)

  def _wait_done_cb(self, f):
    self._emit(*self._cache)


throttle=build_operator(Throttle)