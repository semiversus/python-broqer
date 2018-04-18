"""
Catching exceptions of following operators in the pipelines

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

Example with exception:
>>> disposable = s | op.pluck(0) | op.sink(print)

>>> s.emit([1,2,3])
1
>>> s.emit([])
Traceback (most recent call last):
...
IndexError: list index out of range

>>> disposable.dispose()

Now with ``catch_exception``:
>>> s | op.catch_exception(IndexError) | op.pluck(0) | op.sink(print)
<...>

>>> s.emit([1,2,3])
1
>>> s.emit([]) # will cause a exception but will be catched

"""
from typing import Any

from broqer import Publisher

from ._operator import Operator, build_operator


class CatchException(Operator):
    def __init__(self, publisher: Publisher, *exceptions) -> None:
        assert len(exceptions) >= 1, 'need at least one exception'
        Operator.__init__(self, publisher)
        self._exceptions = exceptions

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        try:
            self._emit(*args)
        except self._exceptions:
            pass


catch_exception = build_operator(CatchException)
