# showing simple subscription to streams

from broqer.hub import Hub
from broqer import op

hub=Hub()

def log(prefix):
  def _(msg):
    print('%s: "%s"'%(prefix, msg))
  return _

message=hub['a.b.message'].setup(retain='Start')

message|op.sink(log('Sink1')) # client2 is subscribing (returns a disposable - here not used)
message.emit('Example doing subscribe and then propose') # client1 is emiting a new value
message|op.sink(log('Sink2'))

hub.unsubscribe_all() # reset hub (clear all streams)