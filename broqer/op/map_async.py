import asyncio
from typing import Any, Coroutine, Optional

from broqer import Publisher

from ._operator import Operator, build_operator


class MapAsync(Operator):
  def __init__(self, publisher:Publisher, map_coro):
    # TODO: supporting various modes when coroutine is running while next value is emitted
    # concurrent - just run coroutines concurrent
    # replace - cancel running and call for new value
    # queue - queue the value(s) and call after coroutine is finished
    # last - use last emitted value after coroutine is finished
    # skip - skip values emitted during coroutine is running
    Operator.__init__(self, publisher)
    self._map_coro=map_coro
    self._future=None
  
  def emit(self, *args:Any, who:Publisher) -> None:
    self._future=asyncio.ensure_future(self._map_coro(*args))
    self._future.add_done_callback(self._future_done)
  
  def _future_done(self, future):
    if future.done():
      *args,_=future.result(),None
      try:
          *args,=args[0]
      except TypeError:
          if args[0] is None:
              args=()
      self._emit(*args)
    else:
      #TODO how to handle an exception?
      pass

map_async=build_operator(MapAsync)