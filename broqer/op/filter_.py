"""
Filters values based on a ``predicate`` function

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> filtered_publisher = s | op.Filter(lambda v:v>0)
>>> _disposable = filtered_publisher | op.Sink(print)

>>> s.emit(1)
1
>>> s.emit(-1)
>>> s.emit(0)
>>> _disposable.dispose()

Also possible with additional args and kwargs:

>>> import operator
>>> filtered_publisher = s | op.Filter(operator.and_, 0x01)
>>> _disposable = filtered_publisher | op.Sink(print)
>>> s.emit(100)
>>> s.emit(101)
101

"""
import asyncio
from functools import partial, wraps
from typing import Any, Callable

from broqer import Publisher

from .operator import Operator


class Filter(Operator):
    """ Filters values based on a ``predicate`` function
    :param publisher: source publisher
    :param predicate: function to evaluate the filtering
    :param \\*args: variable arguments to be used for evaluating predicate
    :param unpack: value from emits will be unpacked as (*value)
    :param \\**kwargs: keyword arguments to be used for evaluating predicate
"""
    def __init__(self, predicate: Callable[[Any], bool],
                 *args, unpack: bool = False, **kwargs) -> None:

        Operator.__init__(self)
        self._predicate = partial(predicate, *args, **kwargs)  # type: Callable
        self._unpack = unpack

    def get(self):
        value = self._publisher.get()  # may raise ValueError
        if (self._unpack and self._predicate(*value)) or \
                (not self._unpack and self._predicate(value)):
            return value
        return Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'

        if self._unpack:
            if self._predicate(*value):
                return self.notify(value)
        elif self._predicate(value):
            return self.notify(value)
        return None


class True_(Operator):  # pylint: disable=invalid-name
    """ Filters all emits which evaluates for True """
    def get(self):
        value = self._publisher.get()  # may raise ValueError
        if bool(value):
            return value
        return Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'
        if bool(value):
            return self.notify(value)
        return None


class False_(Operator):  # pylint: disable=invalid-name
    """ Filters all emits which evaluates for False """
    def get(self):
        value = self._publisher.get()  # may raise ValueError
        if not bool(value):
            return value
        return Publisher.get(self)  # raises ValueError

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'
        if not bool(value):
            return self.notify(value)
        return None


def build_filter(predicate: Callable[[Any], bool] = None, *,
                 unpack: bool = False):
    """ Decorator to wrap a function to return a Filter operator.

    :param predicate: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_filter(predicate: Callable[[Any], bool]):
        @wraps(predicate)
        def _wrapper(*args, **kwargs) -> Filter:
            if 'unpack' in kwargs:
                raise TypeError('"unpack" has to be defined by decorator')
            return Filter(predicate, *args, unpack=unpack, **kwargs)
        return _wrapper

    if predicate:
        return _build_filter(predicate)

    return _build_filter
