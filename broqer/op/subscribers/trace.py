from functools import partial
from typing import Any, Callable, Optional

from broqer import Disposable, Publisher, Subscriber

from broqer.op.operator import build_operator


class Trace(Subscriber, Disposable):
    def __init__(self, publisher: Publisher,
                 sink_function: Optional[Callable[..., None]] = None,
                 *args, unpack=False, **kwargs) -> None:
        if sink_function is None:
            self._sink_function = None  # type: Callable
        elif args or kwargs:
            self._sink_function = \
                partial(sink_function, *args, **kwargs)  # type: Callable
        else:
            self._sink_function = sink_function  # type: Callable

        self._unpack = unpack
        self._disposable = publisher.subscribe(self, prepend=True)

    def emit(self, value: Any, who: Publisher):
        # handle special case: _disposable is set after
        # publisher.subscribe(self) in __init__
        assert not hasattr(self, '_disposable') or \
            who is self._disposable.publisher, \
            'emit comming from non assigned publisher'
        if self._sink_function:
            if self._unpack:
                self._sink_function(*value)
            else:
                self._sink_function(value)

    def dispose(self):
        self._disposable.dispose()


trace = build_operator(Trace)  # pylint: disable=invalid-name
