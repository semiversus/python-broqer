"""
Group ``size`` emitted values overlapping

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> window_publisher = s | op.sliding_window(3)
>>> _d = window_publisher | op.sink(print, 'Sliding Window:')
>>> s.emit(1)
>>> s.emit(2)
>>> s.emit(3)
Sliding Window: (1, 2, 3)
>>> with window_publisher | op.sink(print, '2nd subscriber:'):
...     pass
2nd subscriber: (1, 2, 3)
>>> s.emit(4, 5)
Sliding Window: (2, 3, (4, 5))
>>> window_publisher.cache
(2, 3, (4, 5))
>>> window_publisher.flush()
>>> s.emit(5)
>>> _d.dispose()

With emit_partial the state is emitted even when the queue is not full
>>> window_publisher = s | op.sliding_window( \
                                    3, emit_partial=True, packed=False)
>>> _d = window_publisher | op.sink(print, 'Sliding Window', sep=':')
>>> s.emit(1)
Sliding Window:1
>>> with window_publisher | op.sink(print, '2nd subscriber:'):
...     pass
2nd subscriber: 1
>>> s.emit(2)
Sliding Window:1:2
>>> s.emit(3)
Sliding Window:1:2:3
>>> s.emit(4)
Sliding Window:2:3:4
"""
from typing import Any, MutableSequence  # noqa: F401
from collections import deque

from broqer import Publisher, Subscriber, SubscriptionDisposable

from ._operator import Operator, build_operator


class SlidingWindow(Operator):
    def __init__(self, publisher: Publisher, size: int, emit_partial=False,
                 packed=True) -> None:
        assert size > 0, 'size has to be positive'

        Operator.__init__(self, publisher)

        self._cache = deque(maxlen=size)  # type: MutableSequence
        self._emit_partial = emit_partial
        self._packed = packed

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Operator.subscribe(self, subscriber)
        if (self._emit_partial and len(self._cache)) or \
                len(self._cache) == self._cache.maxlen:  # type: ignore
            if self._packed:
                subscriber.emit(tuple(self._cache), who=self)
            else:
                subscriber.emit(*self._cache, who=self)
        return disposable

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        assert len(args) >= 1, 'need at least one argument for sliding window'
        if len(args) == 1:
            self._cache.append(args[0])
        else:
            self._cache.append(args)
        if self._emit_partial or \
                len(self._cache) == self._cache.maxlen:  # type: ignore
            if self._packed:
                self._emit(tuple(self._cache))
            else:
                self._emit(*self._cache)

    def flush(self):
        self._cache.clear()

    @property
    def cache(self):
        return tuple(self._cache)


sliding_window = build_operator(SlidingWindow)
