"""
Group ``size`` emits into one emit as tuple

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> partitioned_publisher = s | op.partition(3)
>>> _d = partitioned_publisher | op.sink(print, 'Partition:')

>>> s.emit(1)
>>> s.emit(2)
>>> s.emit(3)
Partition: (1, 2, 3)
>>> s.emit(4)
>>> s.emit(5, 6)
>>> partitioned_publisher.flush()
Partition: (4, (5, 6))
"""
from typing import Any, MutableSequence  # noqa: F401

from broqer import Publisher

from ._operator import Operator, build_operator


class Partition(Operator):
    def __init__(self, publisher: Publisher, size: int) -> None:
        # use size = 0 for unlimited partition size
        # (only make sense when using .flush() )
        Operator.__init__(self, publisher)

        self._queue = []  # type: MutableSequence
        self._size = size

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        assert len(args) >= 1, 'need at least one argument for partition'
        if len(args) == 1:
            self._queue.append(args[0])
        else:
            self._queue.append(args)
        if self._size and len(self._queue) == self._size:
            self._emit(tuple(self._queue))
            self._queue.clear()

    def flush(self):
        self._emit(tuple(self._queue))
        self._queue.clear()


partition = build_operator(Partition)
