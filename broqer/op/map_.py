"""
Apply ``function(*args, value, **kwargs)`` to each emitted value

Usage:

>>> from broqer import Value, op, Sink
>>> s = Value()

>>> mapped_publisher = s | op.Map(lambda v:v*2)
>>> _disposable = mapped_publisher.subscribe(Sink(print))

>>> s.emit(1)
2
>>> s.emit(-1)
-2
>>> s.emit(0)
0
>>> _disposable.dispose()

Also possible with additional args and kwargs:

>>> import operator
>>> mapped_publisher = s | op.Map(operator.add, 3)
>>> _disposable = mapped_publisher.subscribe(Sink(print))
3
>>> s.emit(100)
103
>>> _disposable.dispose()

>>> _disposable = (s | op.Map(print, 'Output:')).subscribe(\
                                                Sink(print, 'EMITTED'))
Output: 100
EMITTED None
>>> s.emit(1)
Output: 1
EMITTED None
"""
from functools import partial, wraps
from typing import Any, Callable

from broqer import Publisher, NONE
from broqer.publisher import ValueT
from broqer.operator import Operator


class Map(Operator):
    """ Map object applied to publisher

    :param function: function to be applied for each emit
    :param \\*args: variable arguments to be used for calling function
    :param unpack: value from emits will be unpacked (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for calling function
    """
    def __init__(self, function: Callable[[Any], Any], *args,
                 unpack: bool = False, **kwargs) -> None:
        """ Special care for return values:
              - return `None` (or nothing) if you don't want to return a result
              - return `None, ` if you want to return `None`
              - return `(a, b), ` to return a tuple as value
              - every other return value will be unpacked
        """

        Operator.__init__(self)
        self._function = partial(function, *args, **kwargs)
        self._unpack = unpack

    def get(self) -> ValueT:
        if self._subscriptions:
            return self._state

        if self._originator is None:
            raise ValueError('Operator is missing originator')

        value = self._originator.get()  # type: ValueT

        if value is NONE:
            return value

        if self._unpack:
            assert isinstance(value, (list, tuple))
            return self._function(*value)

        return self._function(value)

    def emit(self, value: ValueT, who: Publisher) -> None:
        if who is not self._originator:
            raise ValueError('Emit from non assigned publisher')

        if self._unpack:
            assert isinstance(value, (list, tuple))
            result = self._function(*value)
        else:
            result = self._function(value)

        if result is not NONE:
            return Publisher.notify(self, result)

        return None


def build_map(function: Callable[..., None] = None, *,
              unpack: bool = False):
    """ Decorator to wrap a function to return a Map operator.

    :param function: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_map(function):
        return Map(function, unpack=unpack)

    if function:
        return _build_map(function)

    return _build_map


def build_map_factory(function: Callable[[Any], Any] = None,
                      unpack: bool = False):
    """ Decorator to wrap a function to return a factory for Map operators.

    :param function: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_map(function: Callable[[Any], Any]):
        @wraps(function)
        def _wrapper(*args, **kwargs) -> Map:
            if 'unpack' in kwargs:
                raise TypeError('"unpack" has to be defined by decorator')
            return Map(function, *args, unpack=unpack, **kwargs)
        return _wrapper

    if function:
        return _build_map(function)

    return _build_map
