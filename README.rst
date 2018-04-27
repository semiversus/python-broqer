===================
Python Broqer
===================

.. image:: https://img.shields.io/pypi/v/broqer.svg
        :target: https://pypi.python.org/pypi/broqer

.. image:: https://img.shields.io/travis/semiversus/python-broqer.svg
        :target: https://travis-ci.org/semiversus/python-broqer

.. image:: https://codecov.io/gh/semiversus/python-broqer/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/semiversus/python-broqer
        
.. image:: https://img.shields.io/github/license/semiversus/python-broqer.svg
        :target: https://en.wikipedia.org/wiki/MIT_License
        
Carefully crafted library to operate with continuous streams of data in a reactive style with publish/subscribe and broker functionality.

Synopsis
========

* Pure python implementation without dependencies (except Python 3.5+)
* Operators known from ReactiveX and other streaming frameworks (like distinct_, combine_latest_, ...)
* Supporting ``asyncio`` for time depended operations and using coroutines (e.g. map_async_, debounce_, ...)
* Publishers are *awaitable* (e.g. ``await adc_raw``)
* Compact library (<1000 lines of code), but well documented (>1000 lines of comments)
* Fully unit tested (coverage towards 100%), coding style checked with flake8_, static typing checked with mypy_
* Under MIT license (2018 Günther Jena)

Install
=======

.. code-block:: bash

    pip install broqer

Example
=======

In the first example ``adc_raw`` is a Publisher_ emitting values from an analog digital converter. The value will
be converter (scaled by factor 0.3), sampled and a moving average is applied. Filtering for values greater 1 will
be printed (with the prefix 'Voltage too high:')

.. code-block:: python

    from broqer import op
    import statistics

    ( adc_raw 
      | op.map(lambda v:v*0.3) # apply a function with one argument returning to value multiplied by 0.3
      | op.sample(0.1) # periodically emit the actual value every 0.1 seconds
      | op.sliding_window(4) # append the value to a buffer with 4 elements (and drop the oldest value)
      | op.map(statistics.mean) # use ``statistics.mean`` to calulate the average over the emitted sequence
      | op.filter(lambda v:v>1) # emit only values greater 1
      | op.sink (print, 'Voltage too high:') # call ``print`` with 'Voltage too high:' and the value
    )

.. image:: https://github.com/semiversus/python-broqer/blob/master/docs/example1.svg

Output to ``stdout``:

.. code::

    Voltage too high: 1.25
    Voltage too high: 1.5
    Voltage too high: 1.75
    Voltage too high: 2
    Voltage too high: 2
    Voltage too high: 2
    Voltage too high: 2

API
===

Publishers
----------

A Publisher_ is the source for messages.

+--------------------------+--------------------------------------------------------------+
| Subject_ ()              | Source with ``.emit(*args)`` method to publish a new message |
+--------------------------+--------------------------------------------------------------+
| Value_ (\*init)          | Source with a state (initialized via ``init``)               |
+--------------------------+--------------------------------------------------------------+
| FromIterable_ (iterable) | Use an ``iterable`` and emit each value                      |
+--------------------------+--------------------------------------------------------------+

Using ``asyncio`` event loop:

+------------------------------------+--------------------------------------------------------------------------+
| FromPolling_ (interval, func, ...) | Call ``func(*args, **kwargs)`` periodically and emit the returned values |
+------------------------------------+--------------------------------------------------------------------------+

Operators
---------

+-------------------------------------+-----------------------------------------------------------------------------+
| accumulate_ (func, init)            | Apply ``func(value, state)`` which is returning new state and value to emit |
+-------------------------------------+-----------------------------------------------------------------------------+
| cache_ (\*init)                     | Caching the emitted values to access it via ``.cache`` property             |
+-------------------------------------+-----------------------------------------------------------------------------+
| catch_exception_ (\*exceptions)     | Catching exceptions of following operators in the pipelines                 |
+-------------------------------------+-----------------------------------------------------------------------------+
| combine_latest_ (\*publishers)      | Combine the latest emit of multiple publishers and emit the combination     |
+-------------------------------------+-----------------------------------------------------------------------------+
| distinct_ (\*init)                  | Only emit values which changed regarding to the cached state                |
+-------------------------------------+-----------------------------------------------------------------------------+
| filter_ (predicate, ...)            | Filters values based on a ``predicate`` function                            |
+-------------------------------------+-----------------------------------------------------------------------------+
| map_ (map_func, \*args, \*\*kwargs) | Apply ``map_func(*args, value, **kwargs)`` to each emitted value            |
+-------------------------------------+-----------------------------------------------------------------------------+
| merge_ (\*publishers)               | Merge emits of multiple publishers into one stream                          |
+-------------------------------------+-----------------------------------------------------------------------------+
| pack_ (\*args)                      | Emit a multi-argument emit as tuple of arguments                            |
+-------------------------------------+-----------------------------------------------------------------------------+
| partition_ (size)                   | Group ``size`` emits into one emit as tuple                                 |
+-------------------------------------+-----------------------------------------------------------------------------+
| pluck_ (\*picks)                    | Apply sequence of picks via ``getitem`` to emitted values                   |
+-------------------------------------+-----------------------------------------------------------------------------+
| reduce_ (func, init)                | Apply ``func`` to the current emitted value and the last result of ``func`` |
+-------------------------------------+-----------------------------------------------------------------------------+
| sliding_window_ (size, ...)         | Group ``size`` emitted values overlapping                                   |
+-------------------------------------+-----------------------------------------------------------------------------+
| switch_ (mapping)                   | Emit selected source mapped by ``mapping``                                  |
+-------------------------------------+-----------------------------------------------------------------------------+
| unpack_ (args)                      | Unpacking a sequence of values and use it to emit as arguments              |
+-------------------------------------+-----------------------------------------------------------------------------+

Using ``asyncio`` event loop:

+----------------------------------+-------------------------------------------------------------------------+
| debounce_ (duetime)              | Emit a value only after a given idle time (emits meanwhile are skipped) |
+----------------------------------+-------------------------------------------------------------------------+
| delay_ (delay)                   | Emit every value delayed by the given time                              |
+----------------------------------+-------------------------------------------------------------------------+
| map_async_ (map_coro, mode, ...) | Apply ``map_coro`` to each emitted value allowing async processing      |
+----------------------------------+-------------------------------------------------------------------------+
| sample_ (interval)               | Emit the last received value periodically                               |
+----------------------------------+-------------------------------------------------------------------------+
| throttle_ (duration)             | Rate limit emits by the given time                                      |
+----------------------------------+-------------------------------------------------------------------------+

Subscribers
-----------

A Subscriber_ is the sink for messages.

+----------------------------------+--------------------------------------------------------------+
| sink_ (func, \*args, \*\*kwargs) | Apply ``func(*args, value, **kwargs)`` to each emitted value |
+----------------------------------+--------------------------------------------------------------+
| to_future_ (timeout=None)        | Build a future able to await for                             |
+----------------------------------+--------------------------------------------------------------+
 
Credits
=======

Broqer was inspired by:

* RxPY_: Reactive Extension for Python (by Børge Lanes and Dag Brattli)
* aioreactive_: Async/Await reactive tools for Python (by Dag Brattli)
* streamz_: build pipelines to manage continous streams of data (by Matthew Rocklin)
* MQTT_: M2M connectivity protocol
* Florian Feurstein: spending hours of discussion, coming up with great ideas and help me understand the concepts! 
g
.. _flake8: http://flake8.pycqa.org/en/latest/
.. _mypy: http://mypy-lang.org/
.. _RxPY: https://github.com/ReactiveX/RxPY
.. _aioreactive: https://github.com/dbrattli/aioreactive
.. _streamz: https://github.com/mrocklin/streamz
.. _MQTT: http://mqtt.org/
.. _Subject: https://github.com/semiversus/python-broqer/blob/master/broqer/subject.py
.. _Value: https://github.com/semiversus/python-broqer/blob/master/broqer/subject.py
.. _Publisher: https://github.com/semiversus/python-broqer/blob/master/broqer/core.py
.. _Subscriber: https://github.com/semiversus/python-broqer/blob/master/broqer/core.py
.. _accumulate: https://github.com/semiversus/python-broqer/blob/master/broqer/op/accumulate.py
.. _cache: https://github.com/semiversus/python-broqer/blob/master/broqer/op/cache.py
.. _catch_exception: https://github.com/semiversus/python-broqer/blob/master/broqer/op/catch_exception.py
.. _combine_latest: https://github.com/semiversus/python-broqer/blob/master/broqer/op/combine_latest.py
.. _debounce: https://github.com/semiversus/python-broqer/blob/master/broqer/op/debounce.py
.. _delay: https://github.com/semiversus/python-broqer/blob/master/broqer/op/delay.py
.. _distinct: https://github.com/semiversus/python-broqer/blob/master/broqer/op/distinct.py
.. _filter: https://github.com/semiversus/python-broqer/blob/master/broqer/op/filter.py
.. _FromIterable: https://github.com/semiversus/python-broqer/blob/master/broqer/op/from_iterable.py
.. _FromPolling: https://github.com/semiversus/python-broqer/blob/master/broqer/op/from_polling.py
.. _map_async: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map_async.py
.. _map: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map.py
.. _merge: https://github.com/semiversus/python-broqer/blob/master/broqer/op/merge.py
.. _pack: https://github.com/semiversus/python-broqer/blob/master/broqer/op/pack.py
.. _partition: https://github.com/semiversus/python-broqer/blob/master/broqer/op/partition.py
.. _pluck: https://github.com/semiversus/python-broqer/blob/master/broqer/op/pluck.py
.. _reduce: https://github.com/semiversus/python-broqer/blob/master/broqer/op/reduce.py
.. _sample: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sample.py
.. _sink: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sink.py
.. _sliding_window: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sliding_window.py
.. _switch: https://github.com/semiversus/python-broqer/blob/master/broqer/op/switch.py
.. _throttle: https://github.com/semiversus/python-broqer/blob/master/broqer/op/throttle.py
.. _to_future: https://github.com/semiversus/python-broqer/blob/master/broqer/op/to_future.py
.. _unpack: https://github.com/semiversus/python-broqer/blob/master/broqer/op/unpack.py
