from broqer.base import Publisher, Subscriber
from typing import Any

class Stream(Publisher, Subscriber):
  def emit(self, *args:Any) -> None:
    if self._cache is not None:
      self._cache=args
    for subscription in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscription.emit(*args, who=self)

  def __await__(self):
    return AsFuture(self).__await__()

from broqer.op import AsFuture
Stream.register_operator(AsFuture, 'as_future')