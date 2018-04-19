from typing import Any, Callable

from broqer import Publisher

from ._operator import Operator, build_operator


class Reduce(Operator):
    def __init__(self, publisher: Publisher, func: Callable[[Any, Any], Any],
                 init=None) -> None:
        Operator.__init__(self, publisher)
        self._cache = init

        self._reduce_func = func

    def emit(self, *args: Any, who: Publisher) -> None:
        assert len(args) == 1, \
            'reduce is only possible for emits with single argument'
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._cache is not None:
            self._cache = self._reduce_func(self._cache, args[0])
            self._emit(self._cache)
        else:
            self._cache = args[0]

    @property
    def cache(self):
        return self._cache


reduce = build_operator(Reduce)
