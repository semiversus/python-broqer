import asyncio
import operator
from typing import Any

from broqer import Publisher
from broqer.op.operator import Operator


class _MapConstant(Operator):
    def __init__(self, publisher: Publisher, value, operator) -> None:
        Operator.__init__(self, publisher)
        self._value = value
        self._operator = operator

    def get(self):
        return self._operator(self._publisher.get(), self._value)

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'

        result = self._operator(value, self._value)

        return self.notify(result)


for method in ('__lt__', '__le__', '__eq__', '__ne__', '__ge__', '__gt__',
               '__add__', '__and__', '__lshift__', '__mod__', '__mul__',
               '__pow__', '__rshift__', '__sub__', '__xor__', '__concat__',
               '__contains__', '__getitem__'):
    def _op(a, b, method=method):
        from broqer.op import CombineLatest

        if isinstance(b, Publisher):
            return CombineLatest(a, b, map_=getattr(operator, method))
        else:
            return _MapConstant(a, b, getattr(operator, method))

    setattr(Publisher, method, _op)


class _MapConstantReverse(Operator):
    def __init__(self, publisher: Publisher, value, operator) -> None:
        Operator.__init__(self, publisher)
        self._value = value
        self._operator = operator

    def get(self):
        return self._operator(self._value, self._publisher.get())

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'

        result = self._operator(self._value, value)

        return self.notify(result)


for method, _method in (('__radd__', '__add__'), ('__rand__', '__and__'),
                        ('__rlshift__', '__lhift__'), ('__rmod__', '__mod__'),
                        ('__rmul__', '__mul__'), ('__rpow__', '__pow__'),
                        ('__rrshift__', '__rshift__'), ('__rsub__', '__sub__'),
                        ('__rxor__', '__xor__')):
    def _op(a, b, method=_method):
        return _MapConstantReverse(a, b, getattr(operator, method))

    setattr(Publisher, method, _op)
