"""
>>> from broqer import Subject, op
>>> s1 = Subject()
>>> s2 = Subject()

>>> combination = s1 | op.combine_latest(s2)
>>> disposable = combination | op.sink(print)

CombineLatest is only emitting, when all values are collected:

>>> s1.emit(1)
>>> s2.emit(2)
(1, 2)
>>> s2.emit(3)
(1, 3)

Subscribing to a CombineLatest with all values available is emitting the values
immediate on subscription:

>>> combination | op.sink(print, 'Second sink:')
Second sink: (1, 3)
<...>

"""
import asyncio
from typing import Any, Dict, MutableSequence  # noqa: F401

from broqer import Publisher, Subscriber, UNINITIALIZED, SubscriptionDisposable

from .operator import MultiOperator, build_operator


class CombineLatest(MultiOperator):
    """ Combine the latest emit of multiple publishers and emit the combination

    :param publishers: source publishers
    :param map_: optional function to be called for evaluation of current state
    :param emit_on: publisher or list of publishers - only emitting result when
        emit comes from one of this list. If None, emit on any source
        publisher.
    :param allow_stateless: when True evaluation is also done for stateless
        publishers. A stateless publisher without an emit will be hold as
        UNINITIALIZED.
    """
    def __init__(self, *publishers: Publisher, map_=None, emit_on=None,
                 allow_stateless=False) -> None:
        MultiOperator.__init__(self, *publishers)
        self._partial_state = [
            UNINITIALIZED for _ in publishers]  # type: MutableSequence[Any]
        self._missing = set(publishers)

        if allow_stateless:
            self._stateless_publishers = None
        else:
            self._stateless_publishers = tuple(False for _ in publishers)

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
        self._state = UNINITIALIZED  # type: Any

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = MultiOperator.subscribe(self, subscriber)
        if len(self._subscriptions) == 1:
            if self._stateless_publishers is None:
                self._stateless_publishers = tuple(
                    v is UNINITIALIZED for v in self._partial_state)
                for p, stateless in zip(
                                self._publishers, self._stateless_publishers):
                    if stateless:
                        self._missing.remove(p)
                        if not any(p is _p for _p in self._emit_on):
                            raise ValueError(
                                'Publisher %r seems to be a stateless '
                                'publisher, but is missing in emit_on')
                if self._map:
                    state = self._map(*self._partial_state)
                else:
                    state = tuple(self._partial_state)
                self.notify(state)
        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        MultiOperator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._missing = set(self._publishers)
            self._partial_state = [UNINITIALIZED for _ in self._partial_state]
            self._state = UNINITIALIZED

    def get(self):
        if not self._subscriptions:  # if no subscribers listening
            values = tuple(p.get() for p in self._publishers)
            if self._map:
                return self._map(*values)
            return tuple(values)
        if self._state is not UNINITIALIZED:
            return self._state
        return Publisher.get(self)  # will raise ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert any(who is p for p in self._publishers), \
            'emit from non assigned publisher'

        if self._missing and any(who is p for p in self._missing):
            self._missing.remove(who)

        index = self._index[who]
        if self._partial_state[index] == value:
            # if partial_state has not changed avoid new emit
            return None

        self._partial_state[index] = value

        if not self._missing and any(who is p for p in self._emit_on):
            if self._map:
                state = self._map(*self._partial_state)
            else:
                state = tuple(self._partial_state)

            if state != self._state or self._stateless_publishers[index]:
                self._state = state
                result = self.notify(self._state)
            else:
                result = None

            if any(self._stateless_publishers):
                self._state = UNINITIALIZED
            if self._stateless_publishers[index]:
                self._partial_state[index] = UNINITIALIZED

            return result
        return None


combine_latest = build_operator(CombineLatest)  # pylint: disable=invalid-name
