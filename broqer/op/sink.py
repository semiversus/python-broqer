"""
Apply ``func(*args, value, **kwargs)`` to each emitted value. It's also
possible to omit ``func`` - in this case the publisher will be subscribed, but
no function will be applied.

Usage:
>>> from broqer import Subject, op
>>> s = Subject()

>>> len(s)
0
>>> _d = s | op.sink(print, 'Sink', sep=':')
>>> len(s)
1

>>> s.emit(1)
Sink:1
>>> s.emit(1, 2)
Sink:1:2

>>> _d.dispose()
>>> len(s)
0
"""
from functools import partial
from typing import Any, Callable, Optional

from broqer import Disposable, Publisher, Subscriber

from ._operator import build_operator


class Sink(Subscriber, Disposable):
    def __init__(self, publisher: Publisher,
                 sink_function: Optional[Callable[[Any], None]]=None,
                 *args, **kwargs) -> None:
        if sink_function is None:
            self._sink_function = None  # type: Callable
        elif args or kwargs:
                self._sink_function = \
                    partial(sink_function, *args, **kwargs)  # type: Callable
        else:
                self._sink_function = sink_function  # type: Callable

        self._disposable = publisher.subscribe(self)

    def emit(self, *args: Any, who: Publisher):
        # handle special case: _disposable is set after
        # publisher.subscribe(self) in __init__
        assert not hasattr(self, '_disposable') or \
            who == self._disposable._publisher, \
            'emit comming from non assigned publisher'
        if self._sink_function:
            self._sink_function(*args)

    def dispose(self):
        self._disposable.dispose()


sink = build_operator(Sink)
