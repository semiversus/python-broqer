""" Implementation of abstract Disposable.
"""
from abc import ABCMeta, abstractmethod


class Disposable(metaclass=ABCMeta):
    """
    Implementation of the disposable pattern. A disposable is usually
    returned on resource allocation. Calling .dispose() on the returned
    disposable is freeing the resource.

    Note: Multiple calls to .dispose() have to be handled by the
    implementation.

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
