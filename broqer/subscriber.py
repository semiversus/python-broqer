""" Implementing the Subscriber class """
import asyncio
from abc import ABCMeta, abstractmethod
from typing import Any, Union

from .publisher import Publisher  # noqa: F401
from .disposable import SubscriptionDisposable  # noqa: F401


class Subscriber(metaclass=ABCMeta):  # pylint: disable=too-few-public-methods
    """ A Subscriber is listening to changes of a publisher. As soon as the
    publisher is emitting a value .emit(value) will be called.
    """
    @abstractmethod
    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        """ Send new value to the subscriber
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """

    def __ror__(self, publisher: Publisher
                ) -> Union[SubscriptionDisposable, Publisher, 'Subscriber']:
        return publisher.subscribe(self)
