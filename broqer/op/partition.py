from typing import Any
from collections import deque

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class Partition(Operator):
  def __init__(self, publisher:Publisher, size:int):
    # use size=0 for unlimited partition size (only make sense when using .flush() )
    Operator.__init__(self, publisher)

    self._queue=[]
    self._size=size

  def emit(self, *args:Any, who:Publisher) -> None:
    assert who==self._publisher, 'emit comming from non assigned publisher'
    assert len(args)>=1, 'need at least one argument for partition'
    if len(args)==1:
      self._queue.append(args[0])
    else:
      self._queue.append(args)
    if self._size and len(self._queue)==self._size:
      self._emit(self._queue)
      self._queue.clear()
  
  def flush(self):
    self._emit(self._queue)
    self._queue.clear()


partition=build_operator(Partition)