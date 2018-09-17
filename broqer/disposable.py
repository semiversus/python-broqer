""" Implementation of abstract Disposable and SubscriptionDisposable.
"""
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from broqer import (Publisher,  # noqa: F401 pylint: disable=unused-import
                        Subscriber)


class Disposable(metaclass=ABCMeta):
    """
    Implementation of the disposable pattern. A disposable is usually
    returned on resource allocation. Calling .dispose() on the returned
    disposable is freeing the resource.

        >>> class MyDisposable(Disposable):
        ...     def dispose(self):
        ...         print('DISPOSED')

        >>> with MyDisposable():
        ...     print('working')
        working
        DISPOSED
    """
    @abstractmethod
    def dispose(self) -> None:
        """ .dispose() method has to be overwritten"""

    def __enter__(self):
        """ Called on entry of a new context """
        return self

    def __exit__(self, _type, _value, _traceback):
        """ Called on exit of the context. .dispose() is called here """
        self.dispose()


class SubscriptionDisposable(Disposable):
    """ This disposable is returned on Publisher.subscribe(subscriber).
        :param publisher: publisher the subscription is made to
        :param subscriber: subscriber used for subscription
    """
    def __init__(self, publisher: 'Publisher', subscriber: 'Subscriber') \
            -> None:
        self._publisher = publisher
        self._subscriber = subscriber

    def dispose(self) -> None:
        self._publisher.unsubscribe(self._subscriber)

    @property
    def publisher(self) -> 'Publisher':
        """ Subscripted publisher """
        return self._publisher

    @property
    def subscriber(self) -> 'Subscriber':
        """ Subscriber used in this subscription """
        return self._subscriber
