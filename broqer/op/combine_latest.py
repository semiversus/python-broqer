"""
>>> from broqer import Value, Sink, op
>>> s1 = Value()
>>> s2 = Value()

>>> combination = op.CombineLatest(s1, s2)
>>> disposable = combination.subscribe(Sink(print))

CombineLatest is only emitting, when all values are collected:

>>> s1.emit(1)
>>> s2.emit(2)
(1, 2)
>>> s2.emit(3)
(1, 3)

Subscribing to a CombineLatest with all values available is emitting the values
immediate on subscription:

>>> combination.subscribe(Sink(print, 'Second sink:'))
Second sink: (1, 3)
<...>

"""
from functools import wraps
from typing import Any, Dict, MutableSequence, Callable  # noqa: F401

from broqer import Publisher, Subscriber, NONE

from broqer.operator import MultiOperator


class CombineLatest(MultiOperator):
    """ Combine the latest emit of multiple publishers and emit the combination

    :param publishers: source publishers
    :param map_: optional function to be called for evaluation of current state
    :param emit_on: publisher or list of publishers - only emitting result when
        emit comes from one of this list. If None, emit on any source
        publisher.
    """
    def __init__(self, *publishers: Publisher, map_: Callable[..., Any] = None,
                 emit_on=None) -> None:
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

        # ._index is a lookup table to get the list index based on publisher
        self._index = \
            {p: i for i, p in enumerate(publishers)
             }  # type: Dict[Publisher, int]

        # .emit_on is a set of publishers. When a source publisher is emitting
        # and is not in this set the CombineLatest will not emit a value.
        # If emit_on is None all the publishers will be in the set.
        if isinstance(emit_on, Publisher):
            self._emit_on = (emit_on,)
        else:
            self._emit_on = emit_on

        self._map = map_

    def unsubscribe(self, subscriber: Subscriber) -> None:
        MultiOperator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._missing = set(self._orginators)
            self._partial_state[:] = [NONE for _ in self._partial_state]

    def get(self):
        if self._subscriptions:
            return self._state

        values = tuple(p.get() for p in self._orginators)

        if NONE in values:
            return NONE

        if not self._map:
            return tuple(values)

        return self._map(*values)

    def emit(self, value: Any, who: Publisher) -> None:
        if all(who is not p for p in self._orginators):
            raise ValueError('Emit from non assigned publisher')

        # remove source publisher from ._missing
        self._missing.discard(who)

        index = self._index[who]

        # remember state of this source
        self._partial_state[index] = value

        # if emits from publishers are missing or source of this emit
        # is not one of emit_on -> don't evaluate and notify subscribers

        if self._missing or (self._emit_on is not None and all(
                who is not p for p in self._emit_on)):
            return None

        # evaluate
        if self._map:
            state = self._map(*self._partial_state)
        else:
            state = tuple(self._partial_state)

        # if result of _map() was NONE don't emit
        if state is NONE:
            return None

        self._state = state

        return Publisher.notify(self, state)


def build_combine_latest(map_: Callable[..., Any] = None, *, emit_on=None):
    """ Decorator to wrap a function to return a CombineLatest operator.

    :param emit_on: publisher or list of publishers - only emitting result when
        emit comes from one of this list. If None, emit on any source
        publisher.
    """
    def _build_combine_latest(map_: Callable[..., Any]):
        @wraps(map_)
        def _wrapper(*publishers) -> CombineLatest:
            return CombineLatest(*publishers, map_=map_, emit_on=emit_on)
        return _wrapper

    if map_:
        return _build_combine_latest(map_)

    return _build_combine_latest
