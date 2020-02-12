""" Implementing Value """

import asyncio
from typing import Any, Optional

from .publisher import Publisher, TValue, TValueNONE
from .subscriber import Subscriber
from .types import NONE


class Value(Publisher, Subscriber):
    """
    Value is a publisher and subscriber.

    >>> from broqer import op

    >>> s = Value(0)
    >>> _d = s.subscribe(op.Sink(print))
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

    def reset_state(self, value: TValueNONE = NONE) -> None:
        raise NotImplementedError('Value doesn\'t support .reset_state()')

    def emit(self, value: TValue,
             who: Optional[Publisher] = None  # pylint: disable=unused-argument
             ) -> asyncio.Future:
        return Publisher.notify(self, value)
