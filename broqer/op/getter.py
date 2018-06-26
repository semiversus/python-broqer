from typing import Any, Tuple

from broqer import Subscriber, Publisher, Disposable
from ._operator import build_operator


class Getter(Subscriber, Disposable):
    def __init__(self, publisher: Publisher) -> None:
        self._value = None  # type: Tuple[Any]
        self._publisher = publisher
        publisher.subscribe(self)

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._value = args

    def dispose(self):
        self._publisher.unsubscribe(self)

    @property
    def value(self):
        if self._value is None:
            raise ValueError('No emit occured yet')
        elif len(self._value) == 1:
            return self._value[0]
        else:
            return self._value


getter = build_operator(Getter)


def get(publisher: Publisher):
    with Getter(publisher) as getter:
        return getter.value
