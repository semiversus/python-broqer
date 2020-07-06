"""
Filters values based on a ``predicate`` function

Usage:

>>> from broqer import Value, op, Sink
>>> s = Value()

>>> filtered_publisher = s | op.Filter(lambda v:v>0)
>>> _disposable = filtered_publisher.subscribe(Sink(print))

>>> s.emit(1)
1
>>> s.emit(-1)
>>> s.emit(0)
>>> _disposable.dispose()

Also possible with additional args and kwargs:

>>> import operator
>>> filtered_publisher = s | op.Filter(operator.and_, 0x01)
>>> _disposable = filtered_publisher.subscribe(Sink(print))
>>> s.emit(100)
>>> s.emit(101)
101

"""
from functools import partial, wraps
from typing import Any, Callable

from broqer import NONE, Publisher
from broqer.operator import Operator, OperatorFactory, OperatorMeta


class AppliedFilter(Operator):
    """ Filter object applied to publisher (see Filter) """
    def __init__(self, publisher: Publisher, predicate: Callable[[Any], bool],
                 unpack: bool = False) -> None:
        Operator.__init__(self, publisher)
        self._predicate = predicate
        self._unpack = unpack

    def get(self) -> Any:
        if self._subscriptions:
            return self._state

        value = self._orginator.get()  # type: Any

        if self._unpack:
            # assert isinstance(value, (list, tuple))
            if self._predicate(*value):
                return value

        elif self._predicate(value):
            return value

        return NONE

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        if self._unpack:
            if self._predicate(*value):
                return Publisher.notify(self, value)
        elif self._predicate(value):
            return Publisher.notify(self, value)
        return None


class Filter(OperatorFactory):  # pylint: disable=too-few-public-methods
    """ Filters values based on a ``predicate`` function
    :param predicate: function to evaluate the filtering
    :param \\*args: variable arguments to be used for evaluating predicate
    :param unpack: value from emits will be unpacked (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for evaluating predicate
    """
    def __init__(self, predicate: Callable[[Any], bool],
                 *args, unpack: bool = False, **kwargs) -> None:
        self._predicate = partial(predicate, *args, **kwargs)  # type: Callable
        self._unpack = unpack

    def apply(self, publisher: Publisher):
        return AppliedFilter(publisher, self._predicate, self._unpack)


class EvalTrue(Operator, metaclass=OperatorMeta):
    """ Emits all values which evaluates for True.

    This operator can be used in the pipline style (v | EvalTrue) or as
    standalone operation (EvalTrue(v)).
    """
    def __init__(self, publisher: Publisher) -> None:
        Operator.__init__(self, publisher)

    def get(self) -> Any:
        if self._subscriptions:
            return self._state

        assert isinstance(self._orginator, Publisher)

        value = self._orginator.get()  # type: Any

        if bool(value):
            return value

        return NONE

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        if bool(value):
            return Publisher.notify(self, value)
        return None


class EvalFalse(Operator, metaclass=OperatorMeta):
    """ Filters all emits which evaluates for False.

    This operator can be used in the pipline style (v | EvalFalse or as
    standalone operation (EvalFalse(v))."""
    def __init__(self, publisher: Publisher) -> None:
        Operator.__init__(self, publisher)

    def get(self) -> Any:
        if self._subscriptions:
            return self._state

        assert isinstance(self._orginator, Publisher)

        value = self._orginator.get()  # type: Any

        if not bool(value):
            return value

        return NONE

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        if not bool(value):
            return Publisher.notify(self, value)
        return None


def build_filter(predicate: Callable[[Any], bool] = None, *,
                 unpack: bool = False):
    """ Decorator to wrap a function to return a Filter operator.

    :param function: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_filter(predicate):
        return Filter(predicate, unpack=unpack)

    if predicate:
        return _build_filter(predicate)

    return _build_filter


def build_filter_factory(predicate: Callable[[Any], bool] = None, *,
                         unpack: bool = False):
    """ Decorator to wrap a function to return a factory for Filter operators.

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
