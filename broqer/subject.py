from typing import Any

from broqer import Disposable, Publisher, Subscriber


class Subject(Publisher, Subscriber):
  def emit(self, *args:Any) -> None:
    for subscription in tuple(self._subscriptions):
      # TODO: critical place to think about handling exceptions
      subscription.emit(*args, who=self)