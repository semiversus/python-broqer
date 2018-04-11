# showing simple subscription to streams

from broqer.hub import Hub
from broqer import op

hub=Hub()

message=hub['a.b.message']

message.emit('First Emit')
message|op.sink(print, 'Sink1')
message.emit('Second Emit')
message|op.sink(print, 'Sink2')
message.emit('Third Emit')