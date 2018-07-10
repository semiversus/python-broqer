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
>>> window_publisher.flush()
>>> s.emit(5)
>>> _d.dispose()

With emit_partial the state is emitted even when the queue is not full:

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
from collections import deque
from typing import Any, MutableSequence  # noqa: F401

from broqer import Publisher, Subscriber, SubscriptionDisposable, unpack_args

from ._operator import Operator, build_operator


class SlidingWindow(Operator):
    def __init__(self, publisher: Publisher, size: int, emit_partial=False,
                 packed=True) -> None:
        assert size > 0, 'size has to be positive'

        Operator.__init__(self, publisher)

        self._state = deque(maxlen=size)  # type: MutableSequence
        self.notify_partial = emit_partial
        self._packed = packed

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Operator.subscribe(self, subscriber)
        if (self.notify_partial and self._state) or \
                len(self._state) == self._state.maxlen:  # type: ignore
            if self._packed:
                subscriber.emit(tuple(self._state), who=self)
            else:
                subscriber.emit(*self._state, who=self)
        return disposable

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        assert len(args) >= 1, 'need at least one argument for sliding window'
        self._state.append(unpack_args(*args))
        if self.notify_partial or \
                len(self._state) == self._state.maxlen:  # type: ignore
            if self._packed:
                self.notify(tuple(self._state))
            else:
                self.notify(*self._state)

    def flush(self):
        self._state.clear()


sliding_window = build_operator(SlidingWindow)
