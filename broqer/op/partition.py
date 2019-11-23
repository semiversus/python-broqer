"""
Group ``size`` emits into one emit as tuple

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> partitioned_publisher = s | op.Partition(3)
>>> _d = partitioned_publisher | op.Sink(print, 'Partition:')

>>> s.emit(1)
>>> s.emit(2)
>>> s.emit(3)
Partition: (1, 2, 3)
>>> s.emit(4)
>>> s.emit((5, 6))
>>> partitioned_publisher.flush()
Partition: (4, (5, 6))
"""
import asyncio
from typing import Any, MutableSequence  # noqa: F401

from broqer.publisher import Publisher
from broqer.subscriber import Subscriber

from .operator import Operator


class Partition(Operator):
    """ Group ``size`` emits into one emit as tuple.

    :param size: emits to be collected before emit
    """
    def __init__(self, size: int) -> None:
        # use size = 0 for unlimited partition size
        # (only make sense when using .flush() )
        Operator.__init__(self)

        self._queue = []  # type: MutableSequence
        self._size = size

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Operator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._queue.clear()

    def get(self):
        queue = list(self._queue)
        value = self._publisher.get()  # may raises ValueError
        queue.append(value)
        if self._size and len(queue) == self._size:
            return tuple(queue)
        return Publisher.get(self)  # raises ValueError

    def emit_op(self, value: Any, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        self._queue.append(value)
        if self._size and len(self._queue) == self._size:
            future = self.notify(tuple(self._queue))
            self._queue.clear()
            return future
        return None

    def flush(self):
        """ Emits the current queue and clears the queue """
        self.notify(tuple(self._queue))
        self._queue.clear()
