""" Concat enables concating operators """
from typing import TYPE_CHECKING

from broqer.operator import OperatorFactory, Publisher


class Concat(OperatorFactory):
    def __init__(self, *operators):
        self._operators = operators

    def apply(self, publisher: Publisher) -> Publisher:
        # concat each operator in the following step
        orginator = publisher

        for operator in self._operators:
            orginator = operator.apply(orginator)

        ## the source publisher is the last operator in the chain
        return orginator