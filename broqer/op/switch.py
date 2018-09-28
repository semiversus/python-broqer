"""
Emit a publisher mapped by ``mapping``

Usage:

>>> from broqer import Subject, Value, op
>>> choose = Subject()
>>> s1 = Value(0)
>>> s2 = Subject()

>>> switch_publisher = choose | op.Switch({'a':s1, 'b':s2})
>>> _d = switch_publisher | op.Sink(print)

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

>>> if_publisher = choose | op.Switch([s1, s2])
>>> _d = if_publisher | op.Sink(print)

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
from typing import Any, Dict

from broqer import Publisher, NONE

from .operator import Operator


class Switch(Operator):
    """ Emit a publisher mapped by ``mapping``
    :param mapping: dictionary with value:(Publisher|constant) mapping
    :param default: value emitted if key is not found
    """
    def __init__(self, mapping: Dict[Any, Any], default: Any = NONE) -> None:
        Operator.__init__(self)
        self._key = NONE  # type: Any
        self._selected_publisher = None  # type: Publisher
        self._mapping = mapping
        self._default = default

    def get(self):
        selection = self._publisher.get()  # may raises ValueError
        try:
            item = self._mapping[selection]
        except (IndexError, KeyError, TypeError):
            if self._default is NONE:
                Publisher.get(self)  # raises ValueError
            item = self._default
        if isinstance(item, Publisher):
            return item.get()  # may raises ValueError
        return item

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            assert who is self._selected_publisher, \
                'emit from not selected publisher'
            return self.notify(value)

        if value is self._key:
            return None

        if self._selected_publisher is not None:
            self._selected_publisher.unsubscribe(self)
        self._selected_publisher = None

        try:
            item = self._mapping[value]
        except (IndexError, KeyError, TypeError):
            if self._default is NONE:
                raise ValueError('Key %r and default not defined' % value)
            item = self._default

        self._key = value

        if isinstance(item, Publisher):
            self._selected_publisher = item
            item.subscribe(self)
        else:
            return self.notify(item)

        return None
