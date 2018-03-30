from abc import ABCMeta, abstractmethod
from typing import Any, Optional

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

class Publisher(metaclass=ABCMeta):
  @abstractmethod
  def subscribe(self, subscriber:'Subscriber'):
    return NotImplemented

  @abstractmethod
  def unsubscribe(self, subscriber:'Subscriber') -> None:
    return NotImplemented
  
  @abstractmethod
  def unsubscribe_all(self) -> None:
    return NotImplemented

class Subscriber(metaclass=ABCMeta):
  @abstractmethod
  def emit(self, *args:Any, who:Optional[Publisher]=None) -> None:
    return NotImplemented