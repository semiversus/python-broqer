Operators
=========

================================= ===========
Operator                          Description
================================= ===========
:doc:`operators/accumulate`       Apply func(value, state) which is returning new state and value to emit
:doc:`operators/cache`            Caching the emitted values (make a stateless publisher stateful)
:doc:`operators/catch_exception`  Catching exceptions of following operators in the pipeline
:doc:`operators/combine_latest`   Combine the latest emit of multiple publishers and emit the combination
:doc:`operators/debounce`         Emit a value only after a given idle time (emits meanwhile are skipped).
:doc:`operators/delay`            Emit every value delayed by the given time.
:doc:`operators/filter`           Filters values based on a ``predicate`` function
:doc:`operators/map`              Apply a function to each emitted value
:doc:`operators/map_async`        Apply a coroutine to each emitted value allowing async processing
:doc:`operators/map_threaded`     Apply a blocking function to each emitted value allowing threaded processing
:doc:`operators/merge`            Merge emits of multiple publishers into one stream
:doc:`operators/partition`        Group ``size`` emits into one emit as tuple
:doc:`operators/reduce`           Like ``Map`` but with additional previous result as argument to the function.
:doc:`operators/replace`          Replace each received value by the given value
:doc:`operators/sample`           Emit the last received value periodically
:doc:`operators/sliding_window`   Group ``size`` emitted values overlapping
:doc:`operators/switch`           Emit selected source mapped by ``mapping``
:doc:`operators/throttle`         Rate limit emits by the given time

================================= ===========

.. toctree::
   :hidden:

   operators/accumulate.rst
   operators/cache.rst
   operators/catch_exception.rst
   operators/combine_latest.rst
   operators/debounce.rst
   operators/delay.rst
   operators/filter.rst
   operators/map.rst
   operators/map_async.rst
   operators/map_threaded.rst
   operators/merge.rst
   operators/partition.rst
   operators/reduce.rst
   operators/replace.rst
   operators/sample.rst
   operators/sliding_window.rst
   operators/switch.rst
   operators/throttle.rst
