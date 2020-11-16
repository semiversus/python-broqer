""" Python operators """
from typing import Any as Any_
from functools import partial, reduce
import operator

from broqer import Publisher
from broqer.operator_overloading import MapUnary
from .combine_latest import CombineLatest


class Str(MapUnary):
    """ Implementing the functionality of str() for publishers.

    Usage:
    >>> from broqer import op, Value
    >>> num = Value(0)
    >>> literal = op.Str(num)
    >>> literal.get()
    '0'
    """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, str)


class Bool(MapUnary):
    """ Implementing the functionality of bool() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, bool)


class Not(MapUnary):
    """ Implementing the functionality of not for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, operator.not_)


class Int(MapUnary):
    """ Implementing the functionality of int() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, int)


class Float(MapUnary):
    """ Implementing the functionality of float() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, float)


class Repr(MapUnary):
    """ Implementing the functionality of repr() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, repr)


class Len(MapUnary):
    """ Implementing the functionality of len() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        MapUnary.__init__(self, publisher, len)


def _in(item, container):
    return item in container


class In(CombineLatest):
    """ Implementing the functionality of ``in`` operator for publishers.
    :param item: publisher or constant to check for availability in container.
    :param container: container (publisher or constant)
    """
    def __init__(self, item: Any_, container: Any_) -> None:
        if isinstance(item, Publisher) and isinstance(container, Publisher):
            CombineLatest.__init__(self, item, container, map_=_in)
        elif isinstance(item, Publisher):
            function = partial(_in, container=container)
            CombineLatest.__init__(self, item, map_=function)
        else:
            if not isinstance(container, Publisher):
                raise TypeError('Item or container has to be a publisher')
            function = partial(_in, item)
            CombineLatest.__init__(self, container, map_=function)


def _all(*items):
    return all(items)


class All(CombineLatest):
    """ Implement the functionality of ``all`` operator for publishers.
    One big difference is that ``all`` takes an iterator and ``All`` take a
    variable amount of publishers as arguments.
    :param publishers: Publishers evaluated for all to be True
    """
    def __init__(self, *publishers: Any_) -> None:
        CombineLatest.__init__(self, *publishers, map_=_all)


def _any(*items):
    return any(items)


class Any(CombineLatest):
    """ Implement the functionality of ``any`` operator for publishers.
    One big difference is that ``any`` takes an iterator and ``Any`` take a
    variable amount of publishers as arguments.
    :param publishers: Publishers evaluated for one to be True
    """
    def __init__(self, *publishers: Any_) -> None:
        CombineLatest.__init__(self, *publishers, map_=_any)


def _bitwise_or(*items):
    return reduce(operator.or_, items)


class BitwiseOr(CombineLatest):
    """ Implement the functionality of bitwise or (``|``) operator for
    publishers.
    :param publishers: Publishers evaluated for bitwise or
    """
    def __init__(self, *publishers: Any_) -> None:
        CombineLatest.__init__(self, *publishers, map_=_bitwise_or)


def _bitwise_and(*items):
    return reduce(operator.and_, items)


class BitwiseAnd(CombineLatest):
    """ Implement the functionality of bitwise and (``&``) operator for
    publishers.
    :param publishers: Publishers evaluated for bitwise and
    """
    def __init__(self, *publishers: Any_) -> None:
        CombineLatest.__init__(self, *publishers, map_=_bitwise_and)
