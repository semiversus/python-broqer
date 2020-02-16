""" Concat enables concating operators """
from typing import Any, TYPE_CHECKING

from broqer.operator import Operator
import broqer

if TYPE_CHECKING:
    from broqer import Publisher


class Concat(Operator):
    """ This class is generator a new operator by concatenation of other
    operators.

    :param operators: the operators to concatenate
    """
    def __init__(self, *operators):
        Operator.__init__(self)
        self._operators = operators

    def emit(self, value: Any, who: 'Publisher') -> None:
        return broqer.Publisher.notify(self, value)

    def apply(self, publisher: 'Publisher') -> 'Publisher':
        # concat each operator in the following step
        orginator = publisher

        for operator in self._operators:
            operator.apply(orginator)
            orginator = operator

        # the source publisher is the last operator in the chain
        Operator.apply(self, self._operators[-1])

        return self._operators[-1]
