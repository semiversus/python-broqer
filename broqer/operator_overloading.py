""" This module enables the operator overloading of publishers """
import math
import operator
from typing import Any as Any_

# pylint: disable=cyclic-import
import broqer
from broqer import Publisher
from broqer.operator import Operator


class MapConstant(Operator):
    """ MapConstant TODO Docstring """
    def __init__(self, publisher: Publisher, value, operation) -> None:
        Operator.__init__(self, publisher)
        self._value = value
        self._operation = operation

        if publisher.inherited_type is not None:
            self.inherit_type(publisher.inherited_type)

    def get(self):
        return self._operation(self._orginator.get(), self._value)

    def emit(self, value: Any_, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        result = self._operation(value, self._value)

        return Publisher.notify(self, result)


class MapConstantReverse(Operator):
    """ MapConstantReverse TODO """
    def __init__(self, publisher: Publisher, value, operation) -> None:
        Operator.__init__(self, publisher)
        self._value = value
        self._operation = operation

        if publisher.inherited_type is not None:
            self.inherit_type(publisher.inherited_type)

    def get(self):
        return self._operation(self._value, self._orginator.get())

    def emit(self, value: Any_, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        result = self._operation(self._value, value)

        return Publisher.notify(self, result)


class MapUnary(Operator):
    """ MapUnary TODO """
    def __init__(self, publisher: Publisher, operation) -> None:
        Operator.__init__(self, publisher)
        self._operation = operation

        if publisher.inherited_type is not None:
            self.inherit_type(publisher.inherited_type)

    def get(self):
        return self._operation(self._orginator.get())

    def emit(self, value: Any_, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        result = self._operation(value)

        return Publisher.notify(self, result)


class _GetAttr(Operator):
    def __init__(self, publisher: Publisher, attribute_name) -> None:
        Operator.__init__(self, publisher)
        self._attribute_name = attribute_name
        self._args = None
        self._kwargs = None

        self.inherit_type(publisher.inherited_type)

    def get(self):
        value = self._orginator.get()  # may raise ValueError
        attribute = getattr(value, self._attribute_name)
        if self._args is None:
            return attribute
        return attribute(*self._args, **self._kwargs)

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def emit(self, value: Any_, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        attribute = getattr(value, self._attribute_name)

        if self._args is None:
            return Publisher.notify(self, attribute)

        return Publisher.notify(self, attribute(*self._args, **self._kwargs))


def apply_operator_overloading():
    """ Function to apply operator overloading to Publisher class """
    # operator overloading is (unfortunately) not working for the following
    # cases:
    # int, float, str - should return appropriate type instead of a Publisher
    # len - should return an integer
    # 'x in y' - is using __bool__ which is not working with Publisher
    for method in (
            '__lt__', '__le__', '__eq__', '__ne__', '__ge__', '__gt__',
            '__add__', '__and__', '__lshift__', '__mod__', '__mul__',
            '__pow__', '__rshift__', '__sub__', '__xor__', '__concat__',
            '__getitem__', '__floordiv__', '__truediv__'):
        def _op(operand_left, operand_right, operation=method):
            if isinstance(operand_right, Publisher):
                return broqer.op.CombineLatest(operand_left, operand_right,
                                               map_=getattr(operator,
                                                            operation))
            return MapConstant(operand_left, operand_right,
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
            return MapConstantReverse(operand_left, operand_right,
                                      getattr(operator, operation))

        setattr(Publisher, method, _op)

    for method, _method in (
            ('__neg__', operator.neg), ('__pos__', operator.pos),
            ('__abs__', operator.abs), ('__invert__', operator.invert),
            ('__round__', round), ('__trunc__', math.trunc),
            ('__floor__', math.floor), ('__ceil__', math.ceil)):
        def _op_unary(operand, operation=_method):
            return MapUnary(operand, operation)

        setattr(Publisher, method, _op_unary)

    def _getattr(publisher, attribute_name):
        if not publisher.inherited_type or \
           not hasattr(publisher.inherited_type, attribute_name):
            raise AttributeError('Attribute %r not found' % attribute_name)
        return _GetAttr(publisher, attribute_name)

    setattr(Publisher, '__getattr__', _getattr)
