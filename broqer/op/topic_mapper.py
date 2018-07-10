from typing import MutableMapping, Any

from broqer import Subscriber, Publisher, unpack_args
from broqer.hub import Topic


class TopicMapper(Subscriber):  # pylint: disable=too-few-public-methods
    def __init__(self, mapping: MutableMapping) -> None:
        self._mapping = mapping

    def emit(self, *args: Any, who: Publisher) -> None:
        assert isinstance(who, Topic)
        self._mapping[who.path] = unpack_args(*args)
