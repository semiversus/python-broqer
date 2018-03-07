from broqer.stream import Stream
from collections import defaultdict
from typing import Optional, Union, Any
from types import MappingProxyType

SEP='.' # separator used for hierarchy

class AssignedStream(Stream):
  def __init__(self, hub:'Hub', name:str):
    Stream.__init__(self)
    self._hub=hub
    self._name=name

  @property
  def hub(self):
    return self._hub
  
  @property
  def name(self):
    return self._name

  @property
  def path(self):
    return self._hub._prefix()+self._name
 
class Hub:
  def __init__(self, parent_hub:Optional['Hub']=None, name:str=''):
    self._name=name
    self._parent_hub=parent_hub
    self._streams=dict()
    self._hubs=dict()
  
  @property
  def hubs(self) -> dict:
    return MappingProxyType(self._hubs)
  
  @property
  def streams(self, stream_name) -> dict:
    return MappingProxyType(self._streams)

  @property
  def parent_hub(self):
    return self._parent_hub
  
  @property
  def name(self):
    return self._name
  
  @property
  def path(self):
    if self._parent_hub:
      return self.parent_hub._prefix() + self._name
    elif self._name:
      return self._name
    else:
      return ''
  
  def _prefix(self):
    if self._parent_hub:
      return self._parent_hub._prefix()+self._name+SEP
    elif self._name:
      return self._name+SEP
    else:
      return ''
  
  def __iter__(self):
    for stream in self._streams.values():
      yield stream.path
    for hub in self._hubs.values():
      yield from iter(hub)

  def __getitem__(self, stream_name:str) -> Union[AssignedStream, 'Hub']:
    if SEP in stream_name:
      # if SEP is found get the Hub and do __getitem__ there
      hub_name, stream_path=stream_name.split(sep=SEP, maxsplit=1)
      assert hub_name not in self._streams, 'Could not access as Hub as %r is used for a Stream'%hub_name
      if hub_name not in self._hubs:
        self._hubs[hub_name]=Hub(parent_hub=self, name=hub_name)
      return self._hubs[hub_name][stream_path]
    elif stream_name in self._hubs: # if it's a stream hub
      return self._hubs[stream_name]
    else:
      if stream_name not in self._streams:
        self._streams[stream_name]=AssignedStream(self, stream_name)
      return self._streams[stream_name]

  def unsubscribe_all(self) -> None:
    for stream in self._streams.values():
      stream.unsubscribe_all()
    for hub in self._hubs.values():
      hub.unsubscribe_all()
    self._hubs.clear()
    self._streams.clear()