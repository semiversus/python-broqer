# showing simple subscription to streams

from broqer.hub import Hub
from broqer import op, Subject

hub=Hub()

hub['message']|op.sink(print, 'Sink:')

print(hub['message'].assigned, hub['message'].meta)

s=Subject()
s|hub.publish('message', {'minimum':0}) # or: s|hub['message'] and then hub['message'].meta={...}

hub['message'].emit('Test1')
s.emit('Test2')

print(message.assigned, message.meta)