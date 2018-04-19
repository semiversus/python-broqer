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
        if self._emit_partial or \
                len(self._cache) == self._cache.maxlen:  # type: ignore
            subscriber.emit(self._cache, who=self)
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
                self._emit(self._cache)
            else:
                self._emit(*self._cache)

    def flush(self):
        self._cache.clear()

    @property
    def cache(self):
        return self._cache


sliding_window = build_operator(SlidingWindow)
