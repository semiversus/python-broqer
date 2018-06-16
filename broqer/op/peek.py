from typing import Any

from broqer import Publisher, Subscriber

from ._operator import build_operator


class Peek(Publisher, Subscriber):
    def __init__(self, source_publisher: Publisher,
                 trigger_publisher: Publisher) -> None:
        Publisher.__init__(self)
        self._source_publisher = source_publisher
        self._trigger_publisher = trigger_publisher
        self._trigger_publisher.subscribe(self)
        self._wait_for_emit = False

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who in (self._source_publisher, self._trigger_publisher), \
            'emit from non assigned publisher'

        if who == self._trigger_publisher and not self._wait_for_emit:
            self._source_publisher.subscribe(self)
            self._wait_for_emit = True
        elif who == self._source_publisher and self._wait_for_emit:
            self._emit(*args)
            self._wait_for_emit = False
            self._source_publisher.unsubscribe(self)


peek = build_operator(Peek)
