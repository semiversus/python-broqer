from rx.internal import extensionclassmethod, extensionmethod
from rx.core import Observable, AnonymousObservable

@extensionclassmethod(Observable)
def from_stream(self, stream):
    def subscribe(observer):
        def next_cb(msg):
            observer.on_next(msg)
        disposable=stream.subscribe(next_cb)
        return disposable.dispose
    return AnonymousObservable(subscribe)

@extensionmethod(Observable)
def emit_stream(self, stream):
    source=self
    def subscribe(observer):
        def on_next(msg):
            stream.emit(msg)
            observer.on_next(msg)

        return source.subscribe(on_next)

    return AnonymousObservable(subscribe)

@extensionmethod(Observable)
def dis(self):

    source = self
    
    def subscribe(observer):

        def on_next(value):
            observer.on_next(value)
            print('on_next')

        return source.subscribe(on_next, observer.on_error, observer.on_completed)
    return AnonymousObservable(subscribe)