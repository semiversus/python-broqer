from typing import Any

from broqer.base import Disposable, Publisher, Subscriber


class Subject(Publisher, Subscriber):
  def emit(self, *args:Any) -> None:
    if self._cache is not None:
      self._cache=args
    for subscription in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscription.emit(*args, who=self)
