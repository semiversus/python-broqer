import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber, Disposable

from ._operator import Operator, build_operator


class Delay(Operator):
  def __init__(self, publisher:Publisher, delay:float, loop=None):
    assert delay>=0, 'delay has to be positive'

    Operator.__init__(self, publisher)

    self._delay=delay
    self._loop=loop or asyncio.get_event_loop()

  def emit(self, *args:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    self._loop.call_later(self._delay, self._emit, *args)

delay=build_operator(Delay)