from broqer import Publisher, Subscriber
from collections import defaultdict
from typing import Any, Optional

SEP='.' # separator used for hierarchy

class ProxyPublisher(Publisher, Subscriber):
  def __init__(self):
    Publisher.__init__(self)
    self._publisher=None

  def emit(self, *args:Any, who:Optional[Publisher]=None) -> None:
    if who is not None and who!=self._publisher:
      raise TypeError('Emit from unassigned publisher. Please use |hub[\'...\'] style for assignment')
    self._emit(*args)
  
  def __call__(self, publisher:Publisher) -> 'ProxyPublisher':
    if self._publisher is not None:
      raise ValueError('ProxyPublisher is already assigned')
    self._publisher=publisher
    return self
  
  @property
  def assigned(self):
    return self._publisher is not None
  
  @property
  def meta(self):
    return getattr(self, '_meta', None)
  
  @meta.setter
  def meta(self, meta_dict):
    if hasattr(self, '_meta'):
      raise ValueError('ProxyPublisher already has a meta dict')
    self._meta=meta_dict
  
 
class Hub:
  def __init__(self):
    self._publishers=defaultdict(ProxyPublisher)
  
  def __getitem__(self, path:str) -> ProxyPublisher:
    return self._publishers[path]

class SubordinateHub:
  def __init__(self, hub, prefix):
    self._hub=hub
    self._prefix=prefix
  
  def __getitem__(self, path:str) -> ProxyPublisher:
    return self._publishers[self._prefix+path]