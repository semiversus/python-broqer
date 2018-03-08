from rx.internal import extensionclassmethod, extensionmethod
from rx.core import Observable, AnonymousObservable
from broqer.stream import Stream
from typing import Any, Optional

@extensionclassmethod(Observable)
def from_stream(self, stream):
  def subscribe(observer):
    class RxStream(Stream):
      def emit(self, *args:Any, who:Optional['Stream']=None) -> None:
        if len(args)==1:
          args=args[0]
        observer.on_next(args)
    disposable=stream.subscribe(RxStream())
    return disposable.dispose
  return AnonymousObservable(subscribe)

@extensionmethod(Observable)
def emit_stream(self, stream, unpack=False):
  source=self
  def subscribe(observer):
    def on_next(args):
      if unpack:
        stream.emit(*args)
      else:
        stream.emit(args)
      observer.on_next(args)
    return source.subscribe(on_next)
  return AnonymousObservable(subscribe)