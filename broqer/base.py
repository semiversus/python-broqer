from abc import ABCMeta, abstractmethod
from typing import Any, Optional, Callable, Union

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
  def setup(self, *cache:Any, meta:Optional[dict]=None) -> 'Publisher':
    self._cache=cache
    self._meta=meta
    return self

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
  def cache(self):
    return self._cache

  @property
  def meta(self):
    return self._meta
  
  @meta.setter
  def meta(self, meta_dict:dict):
    if hasattr(self, '_meta'):
      raise ValueError('Publisher setup already done')
    self._meta=meta_dict
  
  @classmethod
  def register_operator(cls, operator_cls, name):
    def op(source_stream, *args, **kwargs):
      return operator_cls(source_stream, *args, **kwargs)
    setattr(cls, name, op)
  
  def __or__(self, sink:Union['Subscriber', Callable[['Publisher'], 'Publisher']]) -> 'Publisher':
    if isinstance(sink, Subscriber):
      return self.subscribe(sink)
    else:
      return sink(self)

class Subscriber(metaclass=ABCMeta):
  @abstractmethod
  def emit(self, *args:Any, who:Optional[Publisher]=None) -> None:
    return NotImplemented