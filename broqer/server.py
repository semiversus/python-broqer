import asyncio
from broqer.op import Sink

def buildBroqerProtocol(hub):
  def _():
    return BroqerProtocol(hub)
  return _

class BroqerProtocol(asyncio.Protocol):
  def __init__(self, hub):
    self._hub=hub
    self._subscriptions={}

  def connection_made(self, transport):
    self._transport=transport
  
  def connection_lost(self, exc):
    for disposable in self._subscriptions.values():
      disposable.dispose()
    
  def data_received(self, data):
    # available commands
    # emit:stream:arg[:arg2:arg3]
    # sub:stream
    # unsub:stream
    # lw:stream:value
    # throttle:interval
    # dis
    command, *args=data.decode().strip().split(':')

    try:
      method=getattr(self, 'process_'+command)
    except AttributeError:
      self._transport.write(b'# Unknown command\r\n')
    else:
      method(*args)
  
  def process_emit(self, stream:str, *args:str):
    self._hub[stream].emit(*args)
  
  def process_sub(self, stream:str):
    if stream in self._subscriptions:
      self._transport.write(b'# Already subscripted\r\n')
    else:
      def _emit(*args):
        self._transport.write(b'!'+stream.encode()+b':'+b':'.join([str(arg).encode() for arg in args])+b'\r\n')
      self._subscriptions[stream]=Sink(self._hub[stream], _emit)
  
  def process_unsub(self, stream:str):
    if stream in self._subscriptions:
      self._subscriptions[stream].dispose()
      del self._subscriptions[stream]
    else:
      self._transport.write(b'# Not subscripted\r\n')