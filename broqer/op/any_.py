"""Applying any or all build in function to multiple publishers"""
import asyncio
from typing import Dict, MutableSequence, Callable, Tuple  # noqa: F401
from typing import Any as Any_

from broqer import Publisher, Subscriber

from ._operator import MultiOperator, build_operator


class _MultiPredicate(MultiOperator):
    combination_operator = any  # type: ignore

    def __init__(self, *publishers: Publisher,
                 predicate: Callable[[Any_], bool] = None) -> None:
        MultiOperator.__init__(self, *publishers)

        self._predicate = predicate  # type: Callable

        self._index = \
            {p: i for i, p in enumerate(publishers)
             }  # type: Dict[Publisher, int]

        partial = [None for _ in publishers]  # type: MutableSequence[Any_]
        self._partial = partial
        self._state = None  # type: Tuple[bool]

    def unsubscribe(self, subscriber: Subscriber) -> None:
        MultiOperator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._partial = [None for _ in self._partial]
            self._state = None

    def get(self) -> Tuple:
        if self._state is not None:
            return self._state
        values = tuple(p.get() for p in self._publishers)  # may raise ValueError
        if self._predicate is not None:
            values = (self._predicate(v) for v in values)
        return self.combination_operator(values)

    def emit(self, value: Any_, who: Publisher) -> asyncio.Future:
        assert who in self._publishers, 'emit from non assigned publisher'

        if self._predicate is not None:
            self._partial[self._index[who]] = self._predicate(value)
        else:
            self._partial[self._index[who]] = value
        if None in self._partial:
            return None
        state = self.combination_operator(self._partial)  # type:ignore
        if state != self._state:
            self._state = state
            return self.notify(self._state)
        return None


class Any(_MultiPredicate):
    """Applying any built in to source publishers"""
    pass


any_ = build_operator(Any)  # pylint: disable=invalid-name
