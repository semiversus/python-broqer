from broqer.stream import Stream, StreamDisposable
from typing import Callable, Any, Optional, List
import asyncio

class Operator(Stream):
  def __init__(self, *source_streams:List[Stream]):
    self._source_streams=source_streams
    Stream.__init__(self)

  def subscribe(self, stream:'Stream') -> StreamDisposable:
    if not self._subscriptions:
      for _stream in self._source_streams:
        _stream.subscribe(self)
    return Stream.subscribe(self, stream)
  
  def unsubscribe(self, stream:'Stream') -> None:
    Stream.unsubscribe(self, stream)
    if not self._subscriptions:
      for _stream in self._source_streams:
        _stream.unsubscribe(self)

  def unsubscribe_all(self) -> None:
    Stream.unsubscribe_all(self)
    for _stream in self._source_streams:
        _stream.unsubscribe(self)

class Map(Operator):
  def __init__(self, source_stream, map_func):
    Operator.__init__(self, source_stream)
    self._map_func=map_func

  def emit(self, msg_data:Any, who:Stream):
    self._emit(self._map_func(msg_data))

Stream.register_operator(Map, 'map')

class Sink(Stream):
  def __init__(self, source_stream, sink_function):
    Stream.__init__(self)
    self._sink_function=sink_function
    self._disposable=source_stream.subscribe(self)
  
  def emit(self, msg_data:Any, who:Stream):
    self._sink_function(msg_data)
    self._emit(msg_data)
  
  def dispose(self):
    self._disposable.dispose()

Stream.register_operator(Sink, 'sink')

class Distinct(Operator):
  def __init__(self, source_stream):
    Operator.__init__(self, source_stream)
    self._last_msg=None

  def emit(self, msg_data:Any, who:Stream):
    if msg_data!=self._last_msg:
      self._last_msg=msg_data
      self._emit(msg_data)

Stream.register_operator(Distinct, 'distinct')

class CombineLatest(Operator):
  def __init__(self, *source_streams):
    Operator.__init__(self, *source_streams)
    self._last=[None for _ in source_streams]
    self._missing=set(source_streams)
    # TODO: additional keyword to decide if emit undefined values
  
  def emit(self, msg_data:Any, who:Stream):
    if self._missing and who in self._missing:
      self._missing.remove(who)
    self._last[self._source_streams.index(who)]=msg_data
    if not self._missing:
      self._emit(tuple(self._last))

Stream.register_operator(CombineLatest, 'combine_latest')

class Sample(Operator):
  def __init__(self, source_stream, interval):
    Operator.__init__(self, source_stream)
    self._last_msg=None
    self._loop=asyncio.get_event_loop()
    self._loop.call_later(interval, self._periodic_callback, interval)
    # TODO: start _periodic_callback after first subscription

  def _periodic_callback(self, interval):
    if self._last_msg is not None:
      self._emit(self._last_msg)
    self._loop.call_later(interval, self._periodic_callback, interval)

  def emit(self, msg_data:Any, who:Stream):
    self._last_msg=msg_data

Stream.register_operator(Sample, 'sample')

class GetAsync(Stream):
  def __init__(self, source_stream, timeout=None):
    Stream.__init__(self)
    self._disposable=source_stream.subscribe(self)

    loop=asyncio.get_event_loop()
    self._future=loop.create_future()
    self._future.add_done_callback(self._future_done)
    
    if timeout is not None:
      self._timeout_handle=loop.call_later(timeout, self._timeout)
    else:
      self._timeout_handle=None
      
  def _timeout(self):
    self._future.set_exception(asyncio.TimeoutError)
  
  def _future_done(self, future):
    self._disposable.dispose()
    if self._timeout_handle is not None:
      self._timeout_handle.cancel()

  def __await__(self):
    return self._future.__await__()

  def emit(self, msg_data:Any, who:Stream):
    self._future.set_result(msg_data)
 
Stream.register_operator(GetAsync, 'get_async')

class MapAsync(Operator):
  def __init__(self, source_stream, async_func):
    # TODO: supporting various modes when coroutine is running while next value is emitted
    # concurrent - just run coroutines concurrent
    # replace - cancel running and call for new value
    # queue - queue the value(s) and call after coroutine is finished
    # last - use last emitted value after coroutine is finished
    # skip - skip values emitted during coroutine is running
    Operator.__init__(self, source_stream)
    self._async_func=async_func
    self._future=None
  
  def emit(self, msg_data:Any, who:Stream):
    self._future=asyncio.ensure_future(self._async_func(msg_data))
    self._future.add_done_callback(self._future_done)
  
  def _future_done(self, future):
    if future.done():
      self._emit(future.result())
    else:
      #TODO how to handle an exception?
      pass

Stream.register_operator(MapAsync, 'map_async')

# TODO operators
# accumulate(func, start_state) -> value
# filter(cond)
# rate_limit(interval)
# sliding_window e.g. voltage.sample(0.3).sliding_window(10).map(statistics.mean)
# pluck - choose element
# map_async - start corouine
# switch - select stream