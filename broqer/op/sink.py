from functools import partial
from typing import Any, Callable, Optional

from broqer import Disposable, Publisher, Subscriber

from ._operator import build_operator


class Sink(Subscriber, Disposable):
  def __init__(self, publisher:Publisher, sink_function:Callable[[Any], None], *args, **kwargs):
    if args or kwargs:
        self._sink_function=partial(sink_function, *args, **kwargs)
    else:
        self._sink_function=sink_function

    self._disposable=publisher.subscribe(self)
  
  def emit(self, *args:Any, who:Publisher):
    # handle special case: _disposable is set after publisher.subscribe(self) in __init__
    assert not hasattr(self, '_disposable') or who==self._disposable._publisher, 'emit comming from non assigned publisher'
    self._sink_function(*args)
  
  def dispose(self):
    self._disposable.dispose()

sink=build_operator(Sink)
