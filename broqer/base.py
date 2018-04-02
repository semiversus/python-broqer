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
  def setup(self, *cache:Any, meta:Optional[dict]=None) -> 'Publisher':
    return NotImplemented

  @abstractmethod
  def subscribe(self, subscriber:'Subscriber'):
    return NotImplemented

  @abstractmethod
  def unsubscribe(self, subscriber:'Subscriber') -> None:
    return NotImplemented
  
  @abstractmethod
  def unsubscribe_all(self) -> None:
    return NotImplemented
  
  @property
  @abstractmethod
  def cache(self):
    return NotImplemented

  @property
  @abstractmethod
  def meta(self):
    return NotImplemented
  
  @meta.setter
  @abstractmethod
  def meta(self, meta_dict:dict):
    return NotImplemented

class Subscriber(metaclass=ABCMeta):
  @abstractmethod
  def emit(self, *args:Any, who:Optional[Publisher]=None) -> None:
    return NotImplemented