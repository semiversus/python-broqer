import asyncio
from functools import partial
from typing import Any, Callable, List

from broqer import Publisher, Subscriber, SubscriptionDisposable


class FromPolling(Publisher):
  def __init__(self, interval, poll_func:Callable[[Any], Any], *args, **kwargs):
    super().__init__()
    self._interval=interval
    if args or kwargs:
      self._poll_func=partial(poll_func, *args, **kwargs)
    else:
      self._poll_func=poll_func
    self._call_later_handler=None
      

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=Publisher.subscribe(self, subscriber)
    if self._call_later_handler is None:
      self._poll_callback()
    return disposable
  
  def _poll_callback(self):
    result=self._poll_func()
    if result is None:
      result=()
    elif not isinstance(result, tuple):
      result=(result,)
    self._emit(*result)

    if self._subscriptions:
      self._call_later_handler=asyncio.get_event_loop().call_later(self._interval, self._poll_callback)
    else:
      self._call_later_handler=None
