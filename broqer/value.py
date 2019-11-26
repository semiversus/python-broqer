""" Implementing Value """

import asyncio
from typing import Any, Optional

from .publisher import Publisher
from .subscriber import Subscriber
from .types import NONE


class Value(Publisher, Subscriber):
    """
    Value is a publisher and subscriber.

    >>> from broqer import op

    >>> s = Value(0)
    >>> _d = s | op.Sink(print)
    0
    >>> s.emit(1)
    1
    """
    def __init__(self, init=NONE):
        Publisher.__init__(self, init)
        Subscriber.__init__(self)

    def emit(self, value: Any,
             who: Optional[Publisher] = None  # pylint: disable=unused-argument
             ) -> asyncio.Future:
        return self.notify(value)
