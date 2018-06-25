from typing import Any

from broqer import Subscriber, Publisher, Disposable, build_operator

class Getter(Subscriber, Disposable):
    def __init__(self, publisher: Publisher):
        self._value = None
        self._publisher = publisher

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._value = args

    def dispose(self):
        self._publisher.unsubscribe(self)

    @property
    def value(self):
        if self._value == None:
            raise ValueError('No emit occured yet')
        elif len(self._value) == 1:
            return self._value[0]
        else:
            return self._value


getter = build_operator(Getter)

def get(publisher: Publisher):
    with Getter(publisher) as getter:
        return getter.value
