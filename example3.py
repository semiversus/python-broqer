# using rxpy Observable from stream
# note: .emit is used without .propose

from broqer.hub import Hub
from rx import Observable

hub=Hub()

def on_result_change(msg):
    print('Stream "result" changed: %s'%msg)

hub['result'].sink(on_result_change)

message_observable=Observable.from_stream(hub['message'])
message_observable \
    .combine_latest(Observable.from_stream(hub['value']), lambda m,v:m+' '+str(v)) \
    .do_after_next(print) \
    .emit_stream(hub['result']) \
    .subscribe()

hub['message'].emit('The value is')
hub['value'].emit(5)
hub['value'].emit(7)
hub['message'].emit('So ya see')