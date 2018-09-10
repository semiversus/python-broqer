""" Implements TopicMapper """
from typing import MutableMapping, Any

from broqer import Subscriber, Publisher
from broqer.op.operator import build_operator
from broqer.hub import Topic


class TopicMapper(Subscriber):  # pylint: disable=too-few-public-methods
    """ Subscriber using topics on hub to write a dictionary on emits

    :param mapping: dictionary with topic:value mapping
    """
    def __init__(self, mapping: MutableMapping) -> None:
        self._mapping = mapping

    def emit(self, value: Any, who: Publisher) -> None:
        assert isinstance(who, Topic)
        self._mapping[who.path] = value


topic_mapper = build_operator(TopicMapper)  # pylint: disable=invalid-name
