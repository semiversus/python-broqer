"""
Group ``size`` emitted values overlapping

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> window_publisher = s | op.SlidingWindow(3)
>>> _d = window_publisher | op.Sink(print, 'Sliding Window:')
>>> s.emit(1)
>>> s.emit(2)
>>> s.emit(3)
Sliding Window: (1, 2, 3)
>>> with window_publisher | op.Sink(print, '2nd subscriber:'):
...     pass
2nd subscriber: (1, 2, 3)
>>> s.emit((4, 5))
Sliding Window: (2, 3, (4, 5))
>>> window_publisher.flush()
>>> s.emit(5)
>>> _d.dispose()
"""
import asyncio
from collections import deque
from typing import Any, MutableSequence  # noqa: F401

from broqer import Publisher, Subscriber

from .operator import Operator


class SlidingWindow(Operator):
    """ Group ``size`` emitted values overlapping.

    :param size: size of values to be collected before emit
    :param emit_partial: emit even if queue is not full
    """
    def __init__(self, size: int, emit_partial=False) -> None:
        assert size > 0, 'size has to be positive'

        Operator.__init__(self)

        self._state = deque(maxlen=size)  # type: MutableSequence
        self._emit_partial = emit_partial

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Operator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._state.clear()

    def get(self):
        if not self._subscriptions:
            if self._emit_partial or self._state.maxlen == 1:
                return (self._publisher.get(),)  # may raises ValueError
        if self._emit_partial or \
                len(self._state) == self._state.maxlen:  # type: ignore
            if self._state:
                return tuple(self._state)
        return Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'
        self._state.append(value)
        if self._emit_partial or \
                len(self._state) == self._state.maxlen:  # type: ignore
            return self.notify(tuple(self._state))
        return None

    def flush(self):
        """ Flush the queue - this will emit the current queue """
        if not self._emit_partial and len(self._state) != self._state.maxlen:
            self.notify(tuple(self._state))
        self._state.clear()
