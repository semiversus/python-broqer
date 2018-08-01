"""
Filters values based on a ``predicate`` function

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> filtered_publisher = s | op.filter_(lambda v:v>0)
>>> _disposable = filtered_publisher | op.sink(print)

>>> s.emit(1)
1
>>> s.emit(-1)
>>> s.emit(0)
>>> _disposable.dispose()

Also possible with additional args and kwargs:

>>> import operator
>>> filtered_publisher = s | op.filter_(operator.and_, 0x01)
>>> _disposable = filtered_publisher | op.sink(print)
>>> s.emit(100)
>>> s.emit(101)
101

"""
import asyncio
from functools import partial
from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Filter(Operator):
    def __init__(self, publisher: Publisher,
                 predicate: Callable[[Any], bool] = None,
                 *args, **kwargs) -> None:

        Operator.__init__(self, publisher)

        if predicate is not None and (args or kwargs):
            self._predicate = \
                partial(predicate, *args, **kwargs)  # type: Callable
        else:
            self._predicate = predicate  # type: Callable

    def get(self):
        value = self._publisher.get()  # may raise ValueError
        if self._predicate is None:
            if value:
                return value
        elif self._predicate(value):
            return value
        Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._predicate is None:
            if value:
                return self.notify(value)
        elif self._predicate(value):
            return self.notify(value)
        return None


filter_ = build_operator(Filter)  # pylint: disable=invalid-name
