from functools import partial
from typing import Any, Callable, Optional

from broqer import Disposable, Publisher, Subscriber

from broqer.op.operator import build_operator


class Trace(Subscriber, Disposable):
    def __init__(self,  # pylint: disable=keyword-arg-before-vararg
                 publisher: Publisher,
                 callback: Optional[Callable[..., None]] = None,
                 *args, unpack=False, **kwargs) -> None:
        if callback is None:
            self._callback = None  # type: Callable
        elif args or kwargs:
            self._callback = \
                partial(callback, *args, **kwargs)  # type: Callable
        else:
            self._callback = callback  # type: Callable

        self._unpack = unpack
        self._disposable = publisher.subscribe(self, prepend=True)

    def emit(self, value: Any, who: Publisher):
        # handle special case: _disposable is set after
        # publisher.subscribe(self) in __init__
        assert not hasattr(self, '_disposable') or \
            who is self._disposable.publisher, \
            'emit comming from non assigned publisher'
        if self._callback:
            if self._unpack:
                self._callback(*value)
            else:
                self._callback(value)

    def dispose(self):
        self._disposable.dispose()


trace = build_operator(Trace)  # pylint: disable=invalid-name
