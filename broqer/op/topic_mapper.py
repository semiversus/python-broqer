from typing import MutableMapping, Any

from broqer import Subscriber, Publisher, from_args
from broqer.hub import Topic


class TopicMapper(Subscriber):
    def __init__(self, mapping: MutableMapping) -> None:
        self._mapping = mapping

    def emit(self, *args: Any, who: Publisher) -> None:
        assert isinstance(who, Topic)
        self._mapping[who.path] = from_args(*args)
