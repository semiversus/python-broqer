from broqer.stream import Stream, StreamDisposable
from typing import Callable, Any, Optional, List
import asyncio

def build_stream_operator(operator_cls):
  def _op(*args, **kwargs):
    def _build(source_stream):
      return operator_cls(source_stream, *args, **kwargs)
    return _build
  return _op

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

  def emit(self, *args:Any, who:Stream):
    arg, *args,=self._map_func(*args), None
    self._emit(arg, *args[:-1])

map=build_stream_operator(Map)

class Sink(Stream):
  def __init__(self, source_stream, sink_function):
    Stream.__init__(self)
    self._sink_function=sink_function
    self._disposable=source_stream.subscribe(self)
  
  def emit(self, *args:Any, who:Stream):
    self._sink_function(*args)
    self._emit(*args)
  
  def dispose(self):
    self._disposable.dispose()

sink=build_stream_operator(Sink)

class Distinct(Operator):
  def __init__(self, source_stream):
    Operator.__init__(self, source_stream)
    self._last_msg=None

  def emit(self, *args:Any, who:Stream):
    if args!=self._last_msg:
      self._last_msg=args
      self._emit(*args)

distinct=build_stream_operator

class CombineLatest(Operator):
  def __init__(self, *source_streams):
    Operator.__init__(self, *source_streams)
    self._last=[None for _ in source_streams]
    self._missing=set(source_streams)
    # TODO: additional keyword to decide if emit undefined values
  
  def emit(self, *args:Any, who:Stream):
    if self._missing and who in self._missing:
      self._missing.remove(who)
    self._last[self._source_streams.index(who)]=args
    if not self._missing:
      self._emit(*self._last)

combine_latest=build_stream_operator(CombineLatest)

class Sample(Operator):
  def __init__(self, source_stream, interval):
    Operator.__init__(self, source_stream)
    self._last_msg=None
    self._loop=asyncio.get_event_loop()
    self._loop.call_later(interval, self._periodic_callback, interval)
    # TODO: start _periodic_callback after first subscription

  def _periodic_callback(self, interval):
    if self._last_msg is not None:
      self._emit(*self._last_msg)
    self._loop.call_later(interval, self._periodic_callback, interval)

  def emit(self, *args:Any, who:Stream):
    self._last_msg=args

sample=build_stream_operator(Sample)

class AsFuture(Stream):
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

  def emit(self, *args:Any, who:Stream):
    if len(args)==1:
      self._future.set_result(args[0])
    else:
      self._future.set_result(args)
 
as_future=build_stream_operator(AsFuture)

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
  
  def emit(self, *args:Any, who:Stream):
    self._future=asyncio.ensure_future(self._async_func(*args))
    self._future.add_done_callback(self._future_done)
  
  def _future_done(self, future):
    if future.done():
      arg, *args=future.result(), None
      self._emit(arg, *args[:-1])
    else:
      #TODO how to handle an exception?
      pass

map_async=build_stream_operator(MapAsync)

# TODO operators
# accumulate(func, start_state) -> value
# filter(cond)
# rate_limit(interval)
# sliding_window e.g. voltage.sample(0.3).sliding_window(10).map(statistics.mean)
# pluck - choose element
# map_async - start corouine
# switch - select stream