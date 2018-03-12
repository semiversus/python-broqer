from .as_future import as_future, AsFuture
from .combine_latest import combine_latest, CombineLatest
from .distinct import distinct, Distinct
from .map_async import map_async, MapAsync
from .map import map, Map
from .sample import sample, Sample
from .sink import sink, Sink

# TODO operators
# accumulate(func, start_state) -> value
# filter(cond)
# rate_limit(interval)
# sliding_window e.g. voltage.sample(0.3).sliding_window(10).map(statistics.mean)
# pluck - choose element
# map_async - start corouine
# switch - select stream