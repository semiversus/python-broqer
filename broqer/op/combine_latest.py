"""
>>> from broqer import Subject, op
>>> s1 = Subject()
>>> s2 = Subject()

>>> combination = s1 | op.combine_latest(s2)
>>> disposable = combination | op.Sink(print)

CombineLatest is only emitting, when all values are collected:

>>> s1.emit(1)
>>> s2.emit(2)
(1, 2)
>>> s2.emit(3)
(1, 3)

Subscribing to a CombineLatest with all values available is emitting the values
immediate on subscription:

>>> combination | op.Sink(print, 'Second sink:')
Second sink: (1, 3)
<...>

"""
import asyncio
from typing import Any, Dict, MutableSequence  # noqa: F401

from broqer import Publisher, Subscriber, NONE, SubscriptionDisposable

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
        NONE.
    """
    def __init__(self, *publishers: Publisher, map_=None, emit_on=None,
                 allow_stateless=False) -> None:
        MultiOperator.__init__(self, *publishers)

        # ._partial_state is a list keeping the latest emitted values from
        # each publisher. Stateless publishers will always keep the NONE entry
        # in this list.
        self._partial_state = [
            NONE for _ in publishers]  # type: MutableSequence[Any]

        # ._missing is keeping a set of source publishers which are required to
        # emit a value. This set starts with all source publishers. Stateful
        # publishers are required, stateless publishers not (will be removed
        # in .subscribe).
        self._missing = set(publishers)

        # ._stateless is a tuple of boolean values. The boolean value
        # is telling if the source publisher is stateless.
        # When allow_stateless is False all publishers are handled as stateful
        # sources (._partial_state will store the state). Otherwise the tuple
        # will be set in .subscribe (at that point it's clear which publisher
        # is stateless)
        if allow_stateless:
            self._stateless = None
        else:
            self._stateless = tuple(False for _ in publishers)

        # ._index is a lookup table to get the list index based on publisher
        self._index = \
            {p: i for i, p in enumerate(publishers)
             }  # type: Dict[Publisher, int]

        # .emit_on is a set of publishers. When a source publisher is emitting
        # and is not in this set the CombineLatest will not emit a value.
        # If emit_on is None all the publishers will be in the set.
        if emit_on is None:
            self._emit_on = publishers
        elif isinstance(emit_on, Publisher):
            self._emit_on = (emit_on,)
        else:
            self._emit_on = emit_on

        self._map = map_
        self._state = NONE  # type: Any

    def subscribe(self, subscriber: Subscriber,
                  prepend: bool = False) -> SubscriptionDisposable:

        disposable = MultiOperator.subscribe(self, subscriber, prepend)

        # if there are no source publishers emit an empty tuple on subscription
        if not self._publishers:
            self.notify(())

        # check if ._statless is already definied (will be done on first
        # subscription)
        if self._stateless is not None:
            return disposable

        # when .stateless is not defined check which publishers have emitted
        # during first subscription (checking ._partial_state for NONE)
        self._stateless = tuple(v is NONE for v in self._partial_state)

        # _sp is a set of all stateless publishers
        _sp = set(p for p, s in zip(self._publishers, self._stateless) if s)

        # remove the stateless publishers from ._missing set
        self._missing -= _sp

        # check for statless publishers not in ._emit_on. If emit_on is missing
        # a stateless publisher it would never emit when this publisher is
        # emitting.
        if _sp - set(self._emit_on):
            raise ValueError('All stateless publishers have to be part of '
                             'emit_on')

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        MultiOperator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._missing.update(self._publishers)
            self._partial_state[:] = [NONE for _ in self._partial_state]
            self._state = NONE
            # ._stateless will no be reset as it should not change over time

    def get(self):
        # if all publishers are stateful ._state will be defined
        if self._state is not NONE:
            return self._state

        # get value of all publishers
        values = (p.get() for p in self._publishers)  # may raise ValueError

        if not self._map:
            return tuple(values)

        result = self._map(*values)
        if result is NONE:
            Publisher.get(self)  # raises ValueError
        return result

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert any(who is p for p in self._publishers), \
            'emit from non assigned publisher'

        # remove source publisher from ._missing
        self._missing.discard(who)

        index = self._index[who]

        # remember state of this source
        self._partial_state[index] = value

        # if emits from stateful publishers are missing or source of this emit
        # is not one of emit_on -> don't evaluate and notify subscribers
        if self._missing or all(who is not p for p in self._emit_on):
            # stateless publishers don't keep their state in ._partial_state
            if self._stateless and self._stateless[index]:
                self._partial_state[index] = NONE
            return None

        # evaluate
        if self._map:
            state = self._map(*self._partial_state)
        else:
            state = tuple(self._partial_state)

        # remove stateless publisher emits from ._partial_state
        if self._stateless and self._stateless[index]:
            self._partial_state[index] = NONE

        # if result of _map() was NONE don't emit
        if state is NONE:
            self._state = NONE
            return None

        is_new_state = (state == self._state)

        # store ._state only when all publishers are stateful
        if self._stateless and not any(self._stateless):
            self._state = state

        # check if state has changed or stateless publisher has emitted
        if is_new_state and not self._stateless[index]:
            return None

        return self.notify(state)


combine_latest = build_operator(CombineLatest)  # pylint: disable=invalid-name
