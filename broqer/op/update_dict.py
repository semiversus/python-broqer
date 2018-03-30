from broqer.stream import Stream
from typing import Any, Optional
from .operator import build_stream_operator
from broqer.base import Disposable

class UpdateDict(Stream, Disposable):
  def __init__(self, source_stream:Stream, d:dict, key:Optional[str]=None):
    Stream.__init__(self)
    if key is not None:
      self._key=key
    else:
      self._key=source_stream.path # TODO: this is a hack! Only AssignedStreams has path attribute
    self._dict=d
    self._disposable=source_stream.subscribe(self)
  
  def emit(self, *args:Any, who:Optional[Stream]=None):
    if len(args)==1:
      args=args[0]
    self._dict[self._key]=args
  
  def dispose(self):
    self._disposable.dispose()

update_dict=build_stream_operator(UpdateDict)