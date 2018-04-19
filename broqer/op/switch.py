from typing import Any, List

from broqer import Publisher

from ._operator import Operator, build_operator


class Switch(Operator):
    def __init__(self, selection_publisher,
                 publisher_mapping: List[Publisher]) -> None:
        Operator.__init__(self, selection_publisher)
        self._selection_publisher = selection_publisher
        self._selected_publisher = None
        self._mapping = publisher_mapping

    def emit(self, *args: Any, who: Publisher) -> None:
        if who == self._selection_publisher:
            if args[0] != self._selected_publisher:
                if self._selected_publisher:
                    self._selected_publisher.unsubscribe(self)
                self._selected_publisher = args[0]
                self._mapping[self._selected_publisher].subscribe(self)
        else:
            assert who == self._mapping[self._selected_publisher], \
                'emit from not selected publisher'
            self._emit(*args)


switch = build_operator(Switch)
