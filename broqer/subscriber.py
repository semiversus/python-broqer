""" Implementing the Subscriber class """
from abc import ABCMeta, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from broqer import Publisher


class Subscriber(metaclass=ABCMeta):  # pylint: disable=too-few-public-methods
    """ A Subscriber is listening to changes of a publisher. As soon as the
    publisher is emitting a value .emit(value) will be called.
    """

    @abstractmethod
    def emit(self, value: Any, who: 'Publisher') -> None:
        """ Send new value to the subscriber
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """
