from typing import Any, Callable, Optional

from broqer import Disposable, Publisher, Subscriber

from ._operator import build_operator


class UpdateDict(Subscriber, Disposable):
  def __init__(self, publisher:Publisher, d:dict, key:str):
    self._key=key
    self._dict=d
    self._disposable=publisher.subscribe(self)
  
  def emit(self, *args:Any, who:Optional[Publisher]=None):
    if len(args)==1:
      args=args[0]
    self._dict[self._key]=args
  
  def dispose(self):
    self._disposable.dispose()

update_dict=build_operator(UpdateDict)
