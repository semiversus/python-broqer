from abc import ABCMeta, abstractmethod

class Disposable(metaclass=ABCMeta):
  @abstractmethod
  def dispose(self):
    return NotImplemented

  def __enter__(self):
    pass

  def __exit__(self, type, value, traceback):
    self.dispose()
