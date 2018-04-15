# showing simple subscription to streams

from broqer.hub import Hub
from broqer import op, Value, Subject

hub=Hub()

print(hub['message'].assigned, hub['message'].meta,)

s=Value('nop')

s|op.sink(print, 'Sink2:')
hub['message']|op.sink(print, 'Sink1:')

s|hub.publish('message', {'minimum':0}) # or: s|hub['message'] and then hub['message'].meta={...}

hub['message'].emit('Test1')
s.emit('Test2')

print(hub['message'].assigned, hub['message'].meta)