""" This module enables the operator overloading of publishers """
import asyncio
import operator
from typing import Any

from broqer import Publisher
from broqer.op.operator import Operator


class _MapConstant(Operator):
    def __init__(self, publisher: Publisher, value, operation) -> None:
        Operator.__init__(self)
        self._value = value
        self._operation = operation
        self._publisher = publisher

    def get(self):
        return self._operation(self._publisher.get(), self._value)

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'

        result = self._operation(value, self._value)

        return self.notify(result)


class _MapConstantReverse(Operator):
    def __init__(self, publisher: Publisher, value, operation) -> None:
        Operator.__init__(self)
        self._value = value
        self._operation = operation
        self._publisher = publisher

    def get(self):
        return self._operation(self._value, self._publisher.get())

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'

        result = self._operation(self._value, value)

        return self.notify(result)


def apply_operator_overloading():
    """ Function to apply operator overloading to Publisher class """
    for method in ('__lt__', '__le__', '__eq__', '__ne__', '__ge__', '__gt__',
                   '__add__', '__and__', '__lshift__', '__mod__', '__mul__',
                   '__pow__', '__rshift__', '__sub__', '__xor__', '__concat__',
                   '__getitem__', '__floordiv__',
                   '__truediv__'):
        def _op(operand_left, operand_right, operation=method):
            from broqer.op import CombineLatest

            if isinstance(operand_right, Publisher):
                return CombineLatest(operand_left, operand_right,
                                     map_=getattr(operator, operation))
            return _MapConstant(operand_left, operand_right,
                                getattr(operator, operation))

        setattr(Publisher, method, _op)

    for method, _method in (('__radd__', '__add__'), ('__rand__', '__and__'),
                            ('__rlshift__', '__lshift__'),
                            ('__rmod__', '__mod__'), ('__rmul__', '__mul__'),
                            ('__rpow__', '__pow__'),
                            ('__rrshift__', '__rshift__'),
                            ('__rsub__', '__sub__'), ('__rxor__', '__xor__'),
                            ('__rfloordiv__', '__floordiv__'),
                            ('__rtruediv__', '__truediv__')):
        def _op(operand_left, operand_right, operation=_method):
            return _MapConstantReverse(operand_left, operand_right,
                                       getattr(operator, operation))

        setattr(Publisher, method, _op)
