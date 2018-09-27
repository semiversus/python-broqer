""" Implements Trace subscriber """
from broqer import Publisher, SubscriptionDisposable
from broqer.op import Sink


class Trace(Sink):
    """ Trace is a subscriber used for debugging purpose. On subscription
    it will use the prepend flag to be the first callback called when the
    publisher of interest is emitting.
    :param callback: optional function to call
    :param \\*args: arguments used additionally when calling callback
    :param \\*\\*kwargs: keyword arguments used when calling callback
    :param unpack: value from emits will be unpacked (\\*value)
    """
    def __ror__(self, publisher: Publisher) -> SubscriptionDisposable:
        return publisher.subscribe(self, prepend=True)
