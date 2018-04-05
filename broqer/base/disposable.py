from abc import ABCMeta, abstractmethod


class Disposable(metaclass=ABCMeta):
  """ Implementation of the disposable pattern. Call .dispose() to free
      resource.
  """
  @abstractmethod
  def dispose(self):
    return NotImplemented

  def __enter__(self):
    pass

  def __exit__(self, type, value, traceback):
    self.dispose()


class SubscriptionDisposable(Disposable):
  def __init__(self, publisher:'Publisher', subscriber:'Subscriber') -> None:
    self._publisher=publisher
    self._subscriber=subscriber

  def dispose(self) -> None:
    self._publisher.unsubscribe(self._subscriber)
