# showing simple subscription to streams

from broqer.hub import Hub
from broqer import op, Subject

hub=Hub()

message=hub['a.b.message']
s=Subject()

message.emit('First Emit')
message|op.sink(print, 'Sink1')
message.emit('Second Emit')
message|op.sink(print, 'Sink2')
message.emit('Third Emit')

print(message.assigned)
s|message
s.emit('Test')
print(message.assigned)

for p,s in hub:
  print(p,s)