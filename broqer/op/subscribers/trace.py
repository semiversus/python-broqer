from functools import partial
from typing import Any, Callable, Optional

from broqer import Publisher, Subscriber


class Trace(Subscriber):
    def __init__(self,  # pylint: disable=keyword-arg-before-vararg
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

    def emit(self, value: Any, who: Publisher):
        if self._callback:
            if self._unpack:
                self._callback(*value)
            else:
                self._callback(value)

    def __call__(self, publisher: Publisher):
        return publisher.subscribe(self, prepend=True)
