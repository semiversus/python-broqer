from typing import Any, Optional

from broqer import Publisher, StatefulPublisher, Subscriber


class Subject(Publisher, Subscriber):
    """
    Source with ``.emit(*args)`` method to publish a new message.

    >>> from broqer import op

    >>> s = Subject()
    >>> _d = s | op.sink(print)
    >>> s.emit(1)
    1
    """
    def __init__(self):
        Publisher.__init__(self)
        Subscriber.__init__(self)

    def emit(self, *args: Any, who: Optional[Publisher]=None) -> None:
        self.notify(*args)


class Value(StatefulPublisher, Subscriber):
    """
    Source with a state (initialized via ``init``)

    >>> from broqer import op

    >>> s = Value(0)
    >>> _d = s | op.sink(print)
    0
    >>> s.emit(1)
    1
    >>> s.emit(1, 2)
    1 2
    """
    def __init__(self, *init):
        StatefulPublisher.__init__(self, *init)
        Subscriber.__init__(self)

    def emit(self, *args: Any, who: Optional[Publisher]=None) -> None:
        self.notify(*args)
