import asyncio
import json


def build_broqer_protocol(hub):
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
    # available commands:
    # {"cmd":"emit", "path":"...", "args":[...]}
    # {"cmd":"subscribe", "path":"..."}
    # {"cmd":"unsubscribe", "path":"..."}
    # {"cmd":"last_will", "path":"...", "args":[...]}
    # {"cmd":"disconnect"}
    try:
      request=data.decode()
      request_json=json.loads(request)
    except json.JSONDecodeError:
      self._send_json(error='SYNTAX', request=request)
      return

    try:
      method=getattr(self, 'process_'+request_json['cmd'])
    except AttributeError:
      self._send_json(error='UNKNOWN_CMD', request=request_json)
    else:
      method(**request_json)
  
  def _send_json(self, **data):
    self._transport.write(json.dumps(data).encode())

  def process_emit(self, path, args, **kwargs):
    if args
    try:
      self._hub[path].emit(*args) # TODO: handle exception
    except Exception as e:
      self._send_json(error='EMIT_EXCEPTION', path=path, value=value, exception=str(e))
  
  def process_subscribe(self, path, **kwargs):
    if path in self._subscriptions:
      self._send_json(error='ALREADY_SUBSCRIPTED', path=path)
    else:
      def _emit(*args):
        self._send_json(cmd='emit', path=path, args=args)
      self._subscriptions[path]=Sink(self._hub[path], _emit)
  
  def process_unsubscribe(self, path, **kwargs):
    if path in self._subscriptions:
      self._subscriptions[path].dispose()
      del self._subscriptions[path]
    else:
      self._send_json(error='NOT_SUBSCRIPTED', path=path)
  
  def process_last_will(self, path, value, **kwargs):
    pass
