""" Implementing the Subscriber class """
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from broqer import Publisher


class Subscriber():  # pylint: disable=too-few-public-methods
    """ A Subscriber is listening to changes of a publisher. As soon as the
    publisher is emitting a value .emit(value) will be called.
    """

    def emit(self, value: Any, who: 'Publisher') -> None:
        """ Send new value to the subscriber
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """
        raise NotImplementedError('.emit not implemented')

    def reset_state(self) -> None:
        """ Will be called by assigned publisher, when publisher was called
        to reset its state
        """
