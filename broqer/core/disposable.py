from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from broqer.core import Publisher, Subscriber  # noqa: F401


class Disposable(metaclass=ABCMeta):
    """ Implementation of the disposable pattern. Call .dispose() to free
            resource.

        >>> class MyDisposable(Disposable):
        ...     def dispose(self):
        ...         print('DISPOSED')

        >>> d = MyDisposable()
        >>> d.dispose()
        DISPOSED
        >>> with MyDisposable():
        ...     print('working')
        working
        DISPOSED
    """
    @abstractmethod
    def dispose(self):
        """ .dispose() method has to be overwritten"""

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        self.dispose()


class SubscriptionDisposable(Disposable):
    def __init__(self, publisher: 'Publisher', subscriber: 'Subscriber') \
            -> None:
        self._publisher = publisher
        self._subscriber = subscriber

    def dispose(self) -> None:
        self._publisher.unsubscribe(self._subscriber)

    @property
    def publisher(self):
        return self._publisher

    @property
    def subscriber(self):
        return self._subscriber
