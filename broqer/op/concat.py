""" Concat enables concating operators """
from broqer.operator import OperatorFactory, Publisher


class Concat(OperatorFactory):  # pylint: disable=too-few-public-methods
    """ This class is generator a new operator by concatenation of other
    operators.

    :param operators: the operators to concatenate
    """
    def __init__(self, *operators):
        self._operators = operators

    def apply(self, publisher: Publisher) -> Publisher:
        # concat each operator in the following step
        orginator = publisher

        for operator in self._operators:
            orginator = operator.apply(orginator)

        # the source publisher is the last operator in the chain
        return orginator
