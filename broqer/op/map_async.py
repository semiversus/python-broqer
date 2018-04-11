import asyncio
from typing import Any, Optional
from enum import Enum
from collections import deque

from broqer import Publisher

from ._operator import Operator, build_operator

Mode=Enum('Mode', 'CONCURRENT INTERRUPT QUEUE LAST SKIP')

class MapAsync(Operator):
  def __init__(self, publisher:Publisher, map_coro, mode=Mode.CONCURRENT, error_callback=None):
    """
    mode uses one of the following enumerations:
      * CONCURRENT - just run coroutines concurrent
      * INTERRUPT - cancel running and call for new value
      * QUEUE - queue the value(s) and call after coroutine is finished
      * LAST - use last emitted value after coroutine is finished
      * SKIP - skip values emitted during coroutine is running
    """
    Operator.__init__(self, publisher)
    self._map_coro=map_coro
    self._mode=mode
    self._error_callback=error_callback
    self._future=None

    if mode in (Mode.QUEUE, Mode.LAST):
      self._queue=deque(maxlen=(None if mode==Mode.QUEUE else 1) )
    else: # no queue for CONCURRENT, INTERRUPT and SKIP
      self._queue=None
  
  def emit(self, *args:Any, who:Publisher) -> None:
    if self._mode==Mode.INTERRUPT and self._future is not None:
      self._future.cancel()

    if (self._mode in (Mode.INTERRUPT, Mode.CONCURRENT)
            or self._future is None
            or self._future.done() ):
      self._future=asyncio.ensure_future(self._map_coro(*args))
      self._future.add_done_callback(self._future_done)
    elif self._mode in (Mode.QUEUE, Mode.LAST):
      self._queue.append(args)

  def _future_done(self, future):
    try:
      result=future.result()
    except asyncio.CancelledError:
      pass
    except Exception as e:
      if self._error_callback is not None:
        self._error_callback(e)
    else:
      if result is None:
        result=()
      elif not isinstance(result, tuple):
        result=(result,)
      self._emit(*result)
    
    if self._queue:
      self._future=asyncio.ensure_future(self._map_coro(self._queue.popleft()))
      self._future.add_done_callback(self._future_done)

map_async=build_operator(MapAsync)