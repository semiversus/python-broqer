import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable

from ._operator import Operator, build_operator


class Debounce(Operator):
  def __init__(self, publisher:Publisher, duetime:float, loop=None):
    assert duetime>=0, 'duetime has to be positive'

    Operator.__init__(self, publisher)

    self._duetime=duetime
    self._loop=loop or asyncio.get_event_loop()
    self._call_later_handler=None

  def emit(self, *args:Any, who:Publisher) -> None:
    if self._call_later_handler:
      self._call_later_handler.cancel()
    self._call_later_handler=self._loop.call_later(self._duetime, self._emit, *args)

debounce=build_operator(Debounce)