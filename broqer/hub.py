from broqer import Publisher, Subscriber
from collections import defaultdict
from typing import Any, Optional

SEP='.' # separator used for hierarchy

class ProxyPublisher(Publisher, Subscriber):
  def assign(self, publisher:Publisher):
    publisher.subscribe(self)
  
  def emit(self, *args:Any, who:Optional[Publisher]=None) -> None:
    self._emit(*args)
 
class Hub:
  def __init__(self):
    self._publishers=defaultdict(ProxyPublisher)
  
  def __setitem__(self, path:str, publisher:Publisher):
    if path in self._publishers:
      raise KeyError('A publisher already assigned to %r'%path)
    self._publishers[path].assign(publisher)
  
  def __getitem__(self, path:str) -> ProxyPublisher:
    return self._publishers[path]

  def __iter__(self):
    return self._publishers.__iter__()

class SubordinateHub:
  def __init__(self, hub, prefix):
    self._hub=hub
    self._prefix=prefix
  
  def __setitem__(self, path:str, publisher:Publisher):
    if self.prefix+path in self._hub._publishers:
      raise KeyError('A publisher already assigned to %r'%path)
    self._publishers[self._prefix+path].assign(publisher)
  
  def __getitem__(self, path:str) -> ProxyPublisher:
    return self._publishers[self._prefix+path]