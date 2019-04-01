""" This module enables the operator overloading of publishers """
import asyncio
import math
import operator
from functools import partial, reduce
from typing import Any as Any_

from broqer import Publisher
from broqer.op import CombineLatest
from broqer.op.operator import Operator


class _MapConstant(Operator):
    def __init__(self, publisher: Publisher, value, operation) -> None:
        Operator.__init__(self)
        self._value = value
        self._operation = operation
        self._publisher = publisher

        if publisher.inherited_type is not None:
            self.inherit_type(publisher.inherited_type)

    def get(self):
        return self._operation(self._publisher.get(), self._value)

    def emit_op(self, value: Any_, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        result = self._operation(value, self._value)

        return self.notify(result)


class _MapConstantReverse(Operator):
    def __init__(self, publisher: Publisher, value, operation) -> None:
        Operator.__init__(self)
        self._value = value
        self._operation = operation
        self._publisher = publisher

        if publisher.inherited_type is not None:
            self.inherit_type(publisher.inherited_type)

    def get(self):
        return self._operation(self._value, self._publisher.get())

    def emit_op(self, value: Any_, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        result = self._operation(self._value, value)

        return self.notify(result)


class _MapUnary(Operator):
    def __init__(self, publisher: Publisher, operation) -> None:
        Operator.__init__(self)
        self._operation = operation
        self._publisher = publisher

        if publisher.inherited_type is not None:
            self.inherit_type(publisher.inherited_type)

    def get(self):
        return self._operation(self._publisher.get())

    def emit_op(self, value: Any_, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        result = self._operation(value)

        return self.notify(result)


class _GetAttr(Operator):
    def __init__(self, publisher: Publisher, attribute_name) -> None:
        Operator.__init__(self)
        self._attribute_name = attribute_name
        self._publisher = publisher
        self._args = None
        self._kwargs = None

        self.inherit_type(publisher.inherited_type)

    def get(self):
        value = self._publisher.get()  # may raise ValueError
        attribute = getattr(value, self._attribute_name)
        if self._args is None:
            return attribute
        return attribute(*self._args, **self._kwargs)

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def emit_op(self, value: Any_, who: Publisher) -> asyncio.Future:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        attribute = getattr(value, self._attribute_name)

        if self._args is None:
            return self.notify(attribute)

        return self.notify(attribute(*self._args, **self._kwargs))


def apply_operator_overloading():
    """ Function to apply operator overloading to Publisher class """
    # operator overloading is (unfortunately) not working for the following
    # cases:
    # int, float, str - should return appropriate type instead of a Publisher
    # len - should return an integer
    # "x in y" - is using __bool__ which is not working with Publisher
    for method in (
            '__lt__', '__le__', '__eq__', '__ne__', '__ge__', '__gt__',
            '__add__', '__and__', '__lshift__', '__mod__', '__mul__',
            '__pow__', '__rshift__', '__sub__', '__xor__', '__concat__',
            '__getitem__', '__floordiv__', '__truediv__'):
        def _op(operand_left, operand_right, operation=method):
            if isinstance(operand_right, Publisher):
                return CombineLatest(operand_left, operand_right,
                                     map_=getattr(operator, operation))
            return _MapConstant(operand_left, operand_right,
                                getattr(operator, operation))

        setattr(Publisher, method, _op)

    for method, _method in (
            ('__radd__', '__add__'), ('__rand__', '__and__'),
            ('__rlshift__', '__lshift__'), ('__rmod__', '__mod__'),
            ('__rmul__', '__mul__'), ('__rpow__', '__pow__'),
            ('__rrshift__', '__rshift__'), ('__rsub__', '__sub__'),
            ('__rxor__', '__xor__'), ('__rfloordiv__', '__floordiv__'),
            ('__rtruediv__', '__truediv__')):
        def _op(operand_left, operand_right, operation=_method):
            return _MapConstantReverse(operand_left, operand_right,
                                       getattr(operator, operation))

        setattr(Publisher, method, _op)

    for method, _method in (
            ('__neg__', operator.neg), ('__pos__', operator.pos),
            ('__abs__', operator.abs), ('__invert__', operator.invert),
            ('__round__', round), ('__trunc__', math.trunc),
            ('__floor__', math.floor), ('__ceil__', math.ceil)):
        def _op_unary(operand, operation=_method):
            return _MapUnary(operand, operation)

        setattr(Publisher, method, _op_unary)

    def _getattr(publisher, attribute_name):
        if not publisher.inherited_type or \
           not hasattr(publisher.inherited_type, attribute_name):
            raise AttributeError('Attribute %r not found' % attribute_name)
        return _GetAttr(publisher, attribute_name)

    setattr(Publisher, '__getattr__', _getattr)


class Str(_MapUnary):
    """ Implementing the functionality of str() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        _MapUnary.__init__(self, publisher, str)


class Bool(_MapUnary):
    """ Implementing the functionality of bool() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        _MapUnary.__init__(self, publisher, bool)


class Int(_MapUnary):
    """ Implementing the functionality of int() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        _MapUnary.__init__(self, publisher, int)


class Float(_MapUnary):
    """ Implementing the functionality of float() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        _MapUnary.__init__(self, publisher, float)


class Repr(_MapUnary):
    """ Implementing the functionality of repr() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        _MapUnary.__init__(self, publisher, repr)


class Len(_MapUnary):
    """ Implementing the functionality of len() for publishers. """
    def __init__(self, publisher: Publisher) -> None:
        _MapUnary.__init__(self, publisher, len)


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
