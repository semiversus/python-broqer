from .cache import Cache, cache
from .combine_latest import CombineLatest, combine_latest
from .distinct import Distinct, distinct
from .map import Map, map
from .map_async import MapAsync, map_async
from .sample import Sample, sample
from .sink import Sink, sink
from .sliding_window import SlidingWindow, sliding_window
from .switch import Switch, switch
from .to_future import ToFuture, to_future
from .update_dict import UpdateDict, update_dict

# TODO operators
# accumulate(func, start_state) -> value
# filter(cond)
# debounce and throttle - see https://css-tricks.com/debouncing-throttling-explained-examples/
# pluck - choose element
# switch - select stream
# timeout - emit (a value) when timeout on source has passed
# debug
# reduce
# timestamp, elapsed
# delay
# merge
