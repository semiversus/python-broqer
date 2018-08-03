"""
Emit a publisher mapped by ``mapping``

Usage:

>>> from broqer import Subject, Value, op
>>> choose = Subject()
>>> s1 = Value(0)
>>> s2 = Subject()

>>> switch_publisher = choose | op.switch({'a':s1, 'b':s2})
>>> _d = switch_publisher | op.sink(print)

>>> s1.emit(1)
>>> s2.emit(2)

>>> choose.emit('b')
>>> s1.emit(1)
>>> s2.emit(2)
2
>>> choose.emit('a')
1
>>> _d.dispose()

Also using switch as if-then-else construct is possible.
This is working because False is correpsonding to integer 0, True is 1

>>> if_publisher = choose | op.switch([s1, s2])
>>> _d = if_publisher | op.sink(print)

>>> s1.emit(1)
>>> s2.emit(2)

>>> choose.emit(True)
>>> s1.emit(1)
>>> s2.emit(2)
2
>>> choose.emit(False)
1
"""
import asyncio
from typing import Any, List

from broqer import Publisher, UNINITIALIZED

from ._operator import Operator, build_operator


class Switch(Operator):
    def __init__(self, selection_publisher: Publisher,
                 publisher_mapping: List[Publisher]) -> None:
        Operator.__init__(self, selection_publisher)
        self._selection_publisher = selection_publisher
        self._selected_publisher = UNINITIALIZED
        self._mapping = publisher_mapping

    def get(self):
        selection = self._selected_publisher.get()  # may raises ValueError
        return self._mapping[selection].get()  # may raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        if who == self._selection_publisher:
            if self._mapping[value] != self._selected_publisher:
                if self._selected_publisher is not UNINITIALIZED:
                    self._selected_publisher.unsubscribe(self)  # type: ignore
                self._selected_publisher = self._mapping[value]
                self._selected_publisher.subscribe(self)  # type: ignore
            return None
        assert who == self._selected_publisher, \
            'emit from not selected publisher'
        return self.notify(value)


switch = build_operator(Switch)  # pylint: disable=invalid-name
