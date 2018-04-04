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


class SubscriptionDisposable(Disposable):
  def __init__(self, publisher:'Publisher', subscriber:'Subscriber') -> None:
    self._publisher=publisher
    self._subscriber=subscriber

  def dispose(self) -> None:
    self._publisher.unsubscribe(self._subscriber)


class Publisher():
  def __init__(self):
    self._subscriptions=set()
    self._cache=None
    
  def setup(self, *cache:Any, meta:Optional[dict]=None) -> 'Publisher':
    self._cache=cache
    self._meta=meta
    return self

  def subscribe(self, subscriber:'Subscriber'):
    self._subscriptions.add(subscriber)
    if self._cache is not None:
      subscriber.emit(*self._cache, who=self)
    return SubscriptionDisposable(self, subscriber)

  def unsubscribe(self, subscriber:'Subscriber') -> None:
    self._subscriptions.remove(subscriber)

  @property
  def cache(self):
    return self._cache

  @property
  def meta(self):
    return getattr(self, '_meta', None)
  
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