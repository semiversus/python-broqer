# using callbacks on first and last subscriber of stream

from broqer.hub import Hub

hub=Hub()

def print_cb1(msg):
  print('Subscriber1 got a new message: "%s"'%msg)

def print_cb2(msg):
  print('Subscriber2 got a new message: "%s"'%msg)

def on_subscription(stream, subscribing):
  if subscribing:
    print('Starting subscription')
  else:
    print('Stopping subscription')

def example_subscription_callback():
  message=hub['message']

  message.subscribe(print_cb1) 
  print('Proposing stream...')
  message.propose(subscription_callback=on_subscription)
  subscription2=message.subscribe(print_cb2) 
  message.emit('First Message')

  message.unsubscribe(print_cb1)
  subscription2.dispose()

  hub.unsubscribe_all() # reset hub (clear all streams)

example_subscription_callback()