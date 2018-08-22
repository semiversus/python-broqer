import asyncio
from abc import ABCMeta, abstractmethod
from typing import Any

from broqer.core import Publisher  # noqa: F401


class Subscriber(metaclass=ABCMeta):  # pylint: disable=too-few-public-methods
    @abstractmethod
    def emit(self, value: Any, who: 'Publisher') -> asyncio.Future:
        """Send new value to the subscriber
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """

    def __call__(self, publisher: 'Publisher'):
        return publisher.subscribe(self)
