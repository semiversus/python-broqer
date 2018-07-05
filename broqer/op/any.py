from typing import Dict, MutableSequence, Callable  # noqa: F401
from typing import Any as Any_

from broqer import Publisher

from ._operator import MultiOperator, build_operator


class Any(MultiOperator):
    def __init__(self, *publishers: Publisher,
                 predicate: Callable[[Any_], bool]) -> None:
        MultiOperator.__init__(self, *publishers)

        self._predicate = predicate  # type: Callable

        self._index = \
            {p: i for i, p in enumerate(publishers)
             }  # type: Dict[Publisher, int]

        partial = [None for _ in publishers]  # type: MutableSequence[Any_]
        self._partial = partial

    def emit(self, *args: Any_, who: Publisher) -> None:
        assert who in self._publishers, 'emit from non assigned publisher'

        self._partial[self._index[who]] = self._predicate(*args)
        self.notify(any(self._partial))


any = build_operator(Any)
