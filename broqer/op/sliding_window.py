from typing import Any
from collections import deque

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class SlidingWindow(Operator):
  def __init__(self, publisher:Publisher, size, emit_partial=False):
    assert size>0, 'size has to be positive'

    Operator.__init__(self, publisher)

    self._cache=deque(maxlen=size)
    self._emit_partial=emit_partial

  def subscribe(self, subscriber:Subscriber) -> SubscriptionDisposable:
    disposable=Operator.subscribe(self, subscriber)
    if len(self._cache)==self._cache.maxlen or self._emit_partial:
      subscriber.emit(self._cache, who=self)
    return disposable

  def emit(self, *args:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    assert len(args)>=1, 'need at least one argument for sliding window'
    if len(args)==1:
      self._cache.append(args[0])
    else:
      self._cache.append(args)
    if len(self._cache)==self._cache.maxlen or self._emit_partial:
      self._emit(self._cache)
  
  def flush(self):
    self._cache.clear()
    
  @property
  def cache(self):
    return self._cache

sliding_window=build_operator(SlidingWindow)