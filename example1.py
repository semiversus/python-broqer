from broqer.broker import Broker

broker=Broker()

def print_cb(msg):
  print('Got a new message: "%s"'%msg)

def example_propose_subscribe():
  message=broker['message']

  message.propose() # client1 is proposing a new channel
  message.subscribe(print_cb) # client2 is subscribing (returns a disposable - here not used)
  message.publish('Example doing propose and then subscribe') # client1 is publishing a new value

  broker.purge() # reset broker (clear all topics)

def example_subscribe_propose():
  message=broker['message']

  message.subscribe(print_cb) # client2 is subscribing (returns a disposable - here not used)
  message.propose() # client1 is proposing a new channel
  message.publish('Example doing subscribe and then propose') # client1 is publishing a new value

  broker.purge() # reset broker (clear all topics)

example_propose_subscribe()
example_subscribe_propose()
