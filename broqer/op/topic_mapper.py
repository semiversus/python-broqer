from typing import MutableMapping, Any

from broqer import Subscriber, Publisher
from broqer.hub import Topic


class TopicMapper(Subscriber):
    def __init__(self, mapping: MutableMapping) -> None:
        self._mapping = mapping

    def emit(self, *args: Any, who: Publisher) -> None:
        assert isinstance(who, Topic)
        if len(args) == 1:
            self._mapping[who.path] = args[0]
        else:
            self._mapping[who.path] = args
