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
from typing import Any, List

from broqer import Publisher

from ._operator import Operator, build_operator


class Switch(Operator):
    def __init__(self, selection_publisher: Publisher,
                 publisher_mapping: List[Publisher]) -> None:
        Operator.__init__(self, selection_publisher)
        self._selection_publisher = selection_publisher
        self._selected_publisher = None  # type: Publisher
        self._mapping = publisher_mapping

    def emit(self, *args: Any, who: Publisher) -> None:
        if who == self._selection_publisher:
            if self._mapping[args[0]] != self._selected_publisher:
                if self._selected_publisher:
                    self._selected_publisher.unsubscribe(self)
                self._selected_publisher = self._mapping[args[0]]
                self._selected_publisher.subscribe(self)
        else:
            assert who == self._selected_publisher, \
                'emit from not selected publisher'
            self._emit(*args)


switch = build_operator(Switch)
