""" Implementing Value """

from typing import Any, TYPE_CHECKING

# pylint: disable=cyclic-import
from broqer import Publisher, Subscriber, NONE

if TYPE_CHECKING:
    from broqer.publisher import TValueNONE


class Value(Publisher, Subscriber):
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

    def notify(self, value: Any) -> None:
        raise NotImplementedError('Value doesn\'t support .notify().'
                                  ' Use .emit() instead')

    def reset_state(self, value: 'TValueNONE' = NONE) -> None:
        raise NotImplementedError('Value doesn\'t support .reset_state()')

    def emit(self, value: Any,
             who: Publisher = None) -> None:  # pylint: disable=unused-argument
        return Publisher.notify(self, value)
