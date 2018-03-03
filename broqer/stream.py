from broqer.disposable import Disposable
from typing import Callable, Any, Optional
from types import MappingProxyType

class StreamDisposable(Disposable):
  def __init__(self, stream: 'Stream', callback: Callable[[Any], None]) -> None:
    self._stream=stream
    self._callback=callback

  def dispose(self) -> None:
    self._stream.unsubscribe(self._callback)

class Stream:
  def __init__(self):
    self._subscriptions=set()
    self._meta_dict=dict()
    self._subscription_callback=None

  def propose(self, meta_dict: Optional[dict]=None, subscription_callback:Optional[Callable[['Stream', bool],None]]=None) -> 'Stream':
    assert not self._meta_dict, '_meta_dict is populated -> is this stream already proposed?'
    assert not self._subscription_callback, '_subscription_callback is set -> is this stream already proposed?'

    if meta_dict:
      self._meta_dict.update(meta_dict)
    self._subscription_callback=subscription_callback
    if self._subscription_callback and self._subscriptions:
      self._subscription_callback(self, True)
    return self

  def subscribe(self, callback:Callable[[Any],None]) -> StreamDisposable:
    self._subscriptions.add(callback)
    if self._subscription_callback and len(self._subscriptions)==1:
      self._subscription_callback(self, True)
    return StreamDisposable(self, callback)

  def unsubscribe(self, callback:Callable[[Any],None]) -> None:
    self._subscriptions.remove(callback)
    if self._subscription_callback and not self._subscriptions:
      self._subscription_callback(self, False)
  
  def unsubscribe_all(self) -> None:
    if self._subscription_callback and self._subscriptions:
      self._subscription_callback(self, False)
    self._subscriptions.clear()

  def emit(self, msg_data:Any) -> None:
    for cb in self._subscriptions:
      # TODO: critical place to think about handling exceptions
      cb(msg_data)
 
  @property
  def meta(self):
    return MappingProxyType(self._meta_dict)