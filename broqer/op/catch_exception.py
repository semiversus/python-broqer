"""
>>> from broqer import Subject, op
>>> s = Subject()

Example with exception:

>>> disposable = s | op.map_(lambda s:1/s) | op.Sink(print)

>>> s.emit(1)
1.0
>>> s.emit(0)
Traceback (most recent call last):
...
ZeroDivisionError: division by zero

>>> disposable.dispose()

Now with ``catch_exception``:

>>> excp = ZeroDivisionError
>>> s | op.catch_exception(excp) | op.map_(lambda s:1/s) | op.Sink(print)
<...>

>>> s.emit(1)
1.0
>>> s.emit(0) # will cause a exception but will be catched

"""
import asyncio
from typing import Any

from broqer import Publisher

from .operator import Operator, build_operator


class CatchException(Operator):
    """ Catching exceptions of following operators in the pipelines

    :param publisher: source publisher
    :param exceptions: Exception classes to be catched
    """
    def __init__(self, publisher: Publisher, *exceptions) -> None:
        assert len(exceptions) >= 1, 'need at least one exception'
        Operator.__init__(self, publisher)
        self._exceptions = exceptions

    def get(self):
        return self._publisher.get()

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        assert who is self._publisher, 'emit from non assigned publisher'
        try:
            return self.notify(value)
        except self._exceptions:
            pass
        return None


# pylint: disable=invalid-name
catch_exception = build_operator(CatchException)
