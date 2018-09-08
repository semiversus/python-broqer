"""
Apply ``map_func(*args, value, **kwargs)`` to each emitted value

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> mapped_publisher = s | op.map_(lambda v:v*2)
>>> _disposable = mapped_publisher | op.sink(print)

>>> s.emit(1)
2
>>> s.emit(-1)
-2
>>> s.emit(0)
0
>>> _disposable.dispose()

Also possible with additional args and kwargs:

>>> import operator
>>> mapped_publisher = s | op.map_(operator.add, 3)
>>> _disposable = mapped_publisher | op.sink(print)
>>> s.emit(100)
103
>>> _disposable.dispose()

>>> _disposable = s | op.map_(print, 'Output:') | op.sink(print, 'EMITTED')
>>> s.emit(1)
Output: 1
EMITTED None
"""
import asyncio
from functools import partial
from typing import Any, Callable

from broqer import Publisher, NONE

from .operator import Operator, build_operator


class Map(Operator):
    def __init__(self, publisher: Publisher, map_func: Callable[[Any], Any],
                 *args, unpack=False, **kwargs) -> None:
        """ special care for return values:
              * return `None` (or nothing) if you don't want to return a result
              * return `None, ` if you want to return `None`
              * return `(a, b), ` to return a tuple as value
              * every other return value will be unpacked
        """

        Operator.__init__(self, publisher)

        if args or kwargs:
            self._map_func = \
                partial(map_func, *args, **kwargs)  # type: Callable
        else:
            self._map_func = map_func  # type: Callable

        self._unpack = unpack

    def get(self):
        value = self._publisher.get()  # may raise ValueError

        if self._unpack:
            result = self._map_func(*value)
        else:
            result = self._map_func(value)

        if result is NONE:
            Publisher.get(self)  # raises ValueError

        return result

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'

        if self._unpack:
            result = self._map_func(*value)
        else:
            result = self._map_func(value)

        if result is not NONE:
            return self.notify(result)

        return None


map_ = build_operator(Map)  # pylint: disable=invalid-name
