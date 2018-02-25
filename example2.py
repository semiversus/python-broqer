from broqer.broker import Broker

broker=Broker()

def print_cb1(msg):
  print('Subscriber1 got a new message: "%s"'%msg)

def print_cb2(msg):
  print('Subscriber2 got a new message: "%s"'%msg)

def on_subscription(subscribing):
  if subscribing:
    print('Starting subscription')
  else:
    print('Stopping subscription')

def example_subscription_callback():
  message=broker['message']

  message.subscribe(print_cb1) 
  print('Proposing topic...')
  message.propose(on_subscription_callback=on_subscription)
  subscription2=message.subscribe(print_cb2) 
  message.publish('First Message')

  message.unsubscribe(print_cb1)
  subscription2.dispose()

  broker.purge() # reset broker (clear all topics)

example_subscription_callback()
