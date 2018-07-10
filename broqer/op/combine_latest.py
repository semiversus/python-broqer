"""
Combine the latest emit of multiple publishers and emit the combination

Usage:

>>> from broqer import Subject, op
>>> s1 = Subject()
>>> s2 = Subject()

>>> combination = s1 | op.combine_latest(s2)
>>> disposable = combination | op.sink(print)

CombineLatest is only emitting, when all values are collected:

>>> s1.emit(1)
>>> s2.emit(2)
1 2
>>> s2.emit(3)
1 3

Subscribing to a CombineLatest with all values available is emitting the values
immediatly on subscribtion:

>>> combination | op.sink(print, 'Second sink:')
Second sink: 1 3
<...>

"""
from typing import Any, Dict, MutableSequence, Sequence  # noqa: F401

from broqer import Publisher, Subscriber, unpack_args

from ._operator import MultiOperator, build_operator


class CombineLatest(MultiOperator):
    def __init__(self, *publishers: Publisher, map_=None, emit_on=None
                 ) -> None:
        MultiOperator.__init__(self, *publishers)
        partial = [None for _ in publishers]  # type: MutableSequence[Any]
        self._partial_state = partial
        self._missing = set(publishers)
        self._index = \
            {p: i for i, p in enumerate(publishers)
             }  # type: Dict[Publisher, int]
        self._map = map_
        if emit_on is None:
            self._emit_on = publishers
        else:
            if isinstance(emit_on, Publisher):
                self._emit_on = (emit_on,)
            else:
                self._emit_on = emit_on
        self._state = None  # type: Sequence[Any]

    def unsubscribe(self, subscriber: Subscriber) -> None:
        MultiOperator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._missing = set(self._publishers)
            self._partial_state = [None for _ in self._partial_state]

    def get(self):
        if not self._subscriptions:  # if no subscribers listening
            args = tuple(publisher.get() for publisher in self._publishers)
            if None in args:
                if self._state is not None:
                    return self._state
                return None
            args = tuple(unpack_args(*a) for a in args)
            print('ARGS', args)
            if self._map:
                return (self._map(*args),)
            else:
                return args
        if self._state is not None:
            return self._state

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who in self._publishers, 'emit from non assigned publisher'
        if self._missing and who in self._missing:
            self._missing.remove(who)

        args = unpack_args(*args)

        if self._partial_state[self._index[who]] == args:
            # if partial_state has not changed avoid new emit
            return
        self._partial_state[self._index[who]] = args
        if not self._missing and (who in self._emit_on):
            if self._map:
                state = tuple((self._map(*self._partial_state),))
            else:
                state = tuple(self._partial_state)
            if state != self._state:
                self._state = state
                self.notify(*self._state)


combine_latest = build_operator(CombineLatest)  # pylint: disable=invalid-name
