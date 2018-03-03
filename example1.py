# showing simple subscription to streams and proposing of streams

from broqer.hub import Hub

hub=Hub()

def print_cb(msg):
  print('Got a new message: "%s"'%msg)

def example_propose_subscribe():
  message=hub['message']

  message.propose() # client1 is proposing a new channel
  message.subscribe(print_cb) # client2 is subscribing (returns a disposable - here not used)
  message.emit('Example doing propose and then subscribe') # client1 is emiting a new value

  hub.unsubscribe_all() # reset hub (clear all streams)

def example_subscribe_propose():
  message=hub['a.b.message']

  message.subscribe(print_cb) # client2 is subscribing (returns a disposable - here not used)
  message.propose() # client1 is proposing a new channel
  message.emit('Example doing subscribe and then propose') # client1 is emiting a new value

  hub.unsubscribe_all() # reset hub (clear all streams)

example_propose_subscribe()
example_subscribe_propose()