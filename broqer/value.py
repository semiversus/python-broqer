""" Implementing Value """

from typing import Any

# pylint: disable=cyclic-import
from broqer import Publisher, Subscriber, NONE
from broqer.operator import Operator


class Value(Operator):
    """
    Value is a publisher and subscriber.

    >>> from broqer import Sink

    >>> s = Value(0)
    >>> _d = s.subscribe(Sink(print))
    0
    >>> s.emit(1)
    1
    """
    def __init__(self, init=NONE):
        Publisher.__init__(self, init)
        Subscriber.__init__(self)
        self._originator = None  # type: typing.Optional[Publisher]

    def emit(self, value: Any,
             who: Publisher = None) -> None:  # pylint: disable=unused-argument
        if self._originator is not None and self._originator != who:
            raise ValueError('Emit from non assigned publisher')

        return Publisher.notify(self, value)
