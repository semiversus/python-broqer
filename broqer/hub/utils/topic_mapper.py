""" Implements TopicMapper """
from typing import MutableMapping, Any

from broqer import Subscriber, Publisher
from broqer.hub import Topic


class TopicMapper(Subscriber):  # pylint: disable=too-few-public-methods
    """ Subscriber using topics on hub to write a dictionary on emits

    :param mapping: dictionary with topic:value mapping
    """
    def __init__(self, mapping: MutableMapping) -> None:
        self._mapping = mapping

    def emit(self, value: Any, who: Publisher) -> None:
        if not isinstance(who, Topic):
            raise TypeError('Emitting subject has to be a hub topic')

        self._mapping[who.path] = value
