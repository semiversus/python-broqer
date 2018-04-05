from abc import ABCMeta, abstractmethod
from typing import Any, Optional


class Subscriber(metaclass=ABCMeta):
  @abstractmethod
  def emit(self, *args:Any, who:Optional['Publisher']=None) -> None:
    return NotImplemented
