from .accumulate import Accumulate, accumulate
from .cache import Cache, cache
from .combine_latest import CombineLatest, combine_latest
from .distinct import Distinct, distinct
from .filter import Filter, filter
from .from_iterable import FromIterable
from .map import Map, map
from .pluck import Pluck, pluck
from .reduce import Reduce, reduce
from .sink import Sink, sink
from .sliding_window import SlidingWindow, sliding_window
from .switch import Switch, switch

try:
  import asyncio # load following operators only on asyncio availability
except:
  pass
else:
  from .debounce import Debounce, debounce
  from .delay import Delay, delay
  from .from_polling import FromPolling
  from .sample import Sample, sample
  from .map_async import MapAsync, map_async, Mode
  from .throttle import Throttle, throttle
  from .to_future import ToFuture, to_future

# TODO operators
# timeout - emit (a value) when timeout on source has passed
# debug
# timestamp, elapsed
# merge