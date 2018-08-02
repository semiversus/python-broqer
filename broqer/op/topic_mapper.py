from typing import MutableMapping, Any

from broqer import Subscriber, Publisher
from broqer.hub import Topic


class TopicMapper(Subscriber):  # pylint: disable=too-few-public-methods
    def __init__(self, mapping: MutableMapping) -> None:
        self._mapping = mapping

    def emit(self, value: Any, who: Publisher) -> None:
        assert isinstance(who, Topic)
        self._mapping[who.path] = value
