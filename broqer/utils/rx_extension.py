from rx.internal import extensionclassmethod, extensionmethod
from rx.core import Observable, AnonymousObservable
from broqer.stream import Stream
from typing import Any, Optional

@extensionclassmethod(Observable)
def from_stream(self, stream):
  def subscribe(observer):
    class RxStream(Stream):
      def emit(self, *args:Any, who:Optional['Stream']=None) -> None:
        if len(args)=
        observer.on_next(args)
    disposable=stream.subscribe(RxStream())
    return disposable.dispose
  return AnonymousObservable(subscribe)

@extensionmethod(Observable)
def emit_stream(self, stream):
  source=self
  def subscribe(observer):
    def on_next(args):
      stream.emit(*args)
      observer.on_next(args)
    return source.subscribe(on_next)
  return AnonymousObservable(subscribe)