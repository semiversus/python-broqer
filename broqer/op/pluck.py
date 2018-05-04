"""
Apply sequence of picks via ``getitem`` to emitted values

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

Get element n in an indexable object:
>>> _d = s | op.pluck(0) | op.sink(print, 'Plucked:')
>>> s.emit(['a', 'b', 'c'])
Plucked: a
>>> s.emit([1, 2, 3])
Plucked: 1
>>> _d.dispose()

Get key k in an mapping object:
>>> _d = s | op.pluck('value') | op.sink(print, 'Plucked:')
>>> s.emit({'name':'test', 'value':5})
Plucked: 5
>>> s.emit({'a':0, 'b':1})
Traceback (most recent call last):
...
KeyError: 'value'
>>> _d.dispose()

Get a slice:
>>> _d = s | op.pluck(slice(0, 2)) | op.sink(print, 'Plucked:')
>>> s.emit(['a', 'b', 'c'])
Plucked: ['a', 'b']
>>> s.emit([1, 2, 3])
Plucked: [1, 2]
>>> _d.dispose()

Multiple picks:
>>> _d = s | op.pluck(1, 'value', slice(0, 2)) | op.sink(print, 'Plucked:')
>>> s.emit([{'value':[1, 2, 3]}, {'value':['a', 'b', 'c']}])
Plucked: ['a', 'b']
>>> _d.dispose()
"""
from operator import getitem
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class Pluck(Operator):
    def __init__(self, publisher: Publisher, *picks: Any) -> None:
        assert len(picks) >= 1, 'need at least one pick key'
        Operator.__init__(self, publisher)

        self._picks = picks

    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'pluck is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        arg = args[0]
        for pick in self._picks:
            arg = getitem(arg, pick)
        self._emit(arg)


pluck = build_operator(Pluck)
