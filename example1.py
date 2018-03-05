# showing simple subscription to streams

from broqer.hub import Hub

hub=Hub()

def print_cb(msg):
  print('Got a new message: "%s"'%msg)

message=hub['a.b.message']

message.sink(print_cb) # client2 is subscribing (returns a disposable - here not used)
message.emit('Example doing subscribe and then propose') # client1 is emiting a new value

hub.unsubscribe_all() # reset hub (clear all streams)