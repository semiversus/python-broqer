===================
Python Broqer
===================

.. image:: https://img.shields.io/pypi/v/broqer.svg
  :target: https://pypi.python.org/pypi/broqer

.. image:: https://img.shields.io/travis/semiversus/python-broqer/master.svg
  :target: https://travis-ci.org/semiversus/python-broqer

.. image:: https://readthedocs.org/projects/python-broqer/badge/?version=latest
  :target: https://python-broqer.readthedocs.io/en/latest

.. image:: https://codecov.io/gh/semiversus/python-broqer/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/semiversus/python-broqer

.. image:: https://img.shields.io/github/license/semiversus/python-broqer.svg
  :target: https://en.wikipedia.org/wiki/MIT_License

Initial focus on embedded systems *Broqer* can be used wherever continuous streams of data have to be processed - and they are everywhere. Watch out!

.. image:: https://cdn.rawgit.com/semiversus/python-broqer/7beb7379/docs/logo.svg

Synopsis
========

+--------------------------------------------------------------------------------+
| **Broqer 1.0.0 will be released soon (till end of october 2018) - stay tuned** |
+--------------------------------------------------------------------------------+

- Pure python implementation without dependencies
- Under MIT license (2018 Günther Jena)
- Source is hosted on GitHub.com_
- Documentation is hosted on ReadTheDocs.com_
- Tested on Python 3.5, 3.6, 3.7 and 3.8-dev
- Unit tested with pytest_, coding style checked with Flake8_, static type checked with mypy_, static code checked with Pylint_, documented with Sphinx_
- Operators known from ReactiveX_ and other streaming frameworks (like Map_, CombineLatest_, ...)
- Broker functionality via Hub_

  + Centralised object to keep track of publishers and subscribers
  + Starting point to build applications with a microservice architecture

.. _pytest: https://docs.pytest.org/en/latest
.. _Flake8: http://flake8.pycqa.org/en/latest/
.. _mypy: http://mypy-lang.org/
.. _Pylint: https://www.pylint.org/
.. _Sphinx: http://www.sphinx-doc.org
.. _GitHub.com: https://github.com/semiversus/python-broqer
.. _ReadTheDocs.com: http://python-broqer.readthedocs.io
.. _ReactiveX: http://reactivex.io/
.. _Hub: https://github.com/semiversus/python-broqer/blob/master/broqer/hub/hub.py

.. marker-for-example

Showcase
========

In other frameworks *Publisher* are sometimes called *Oberservable*. A subscriber
is able to observe changes the publisher is emitting. With this basics you're
able to use the observer pattern - let's see!

Observer pattern
----------------

Subscribing to a publisher is done via the ``|`` operator - here used as a pipe.
A simple subscriber is ``op.Sink`` which is calling a function with optional positional
and keyword arguments.

.. code-block:: python3

    >>> from broqer import Value, op
    >>> a = Value(5)  # create a value (publisher and subscriber with state)
    >>> disposable = a | op.Sink(print, 'Change:')  # subscribe a callback
    Change: 5

    >>> a.emit(3)  # change the value
    Change: 3

    >>> disposable.dispose()  # unsubscribe

Combine publishers with arithmetic operators
--------------------------------------------

You're able to create publishers on the fly by combining two publishers with
the common operators (like ``+``, ``>``, ``<<``, ...).

.. code-block:: python3

    >>> from broqer import Value, op
    >>> a = Value(1)
    >>> b = Value(3)

    >>> c = a * 3 > b  # create a new publisher via operator overloading
    >>> c | op.Sink(print, 'c:')
    c: False

    >>> a.emit(1)  # will not change the state of c
    >>> a.emit(2)
    c: True

Also fancy stuff like getting item by index or key is possible:

.. code-block:: python3

    >>> i = Value('a')
    >>> d = Value({'a':100, 'b':200, 'c':300})

    >>> d[i] | op.Sink(print, 'r:')
    r: 100

    >>> i.emit('c')
    r: 300
    >>> d.emit({'c':123})
    r: 123

Asyncio Support
---------------

A lot of operators are made for asynchronous operations. You're able to debounce
and throttle emits (via ``op.Debounce`` and ``op.Throttle``), sample and delay
(via ``op.Sample`` and ``op.Delay``) or start coroutines and when finishing the
result will be emitted.

.. code-block:: python3

    >>> async def long_running_coro(value):
    ...     await asyncio.sleep(3)
    ...     return value + 1
    ...
    >>> a = Value(0)
    >>> a | op.MapAsync(long_running_coro) | op.Sink(print, 'Result:')

After 3 seconds the result will be:

.. code-block:: bash

    Result: 0

``MapAsync`` supports various modes how to handle a new emit when a coroutine
is running. Default is a concurrent run of coroutines, but also various queue
or interrupt mode is available.

Every publisher can be awaited in coroutines:

.. code-block:: python3

    await signal_publisher

Function decorators
-------------------

Make your own operators on the fly with function decorators. Decorators are
available for ``Accumulate``, ``CombineLatest``, ``Filter``, ``Map``, ``MapAsync``,
``MapThreaded``, ``Reduce`` and ``Sink``.

.. code-block:: python3

    >>> @build_map
    ... def count_vowels(s):
    ...     return sum([s.count(v) for v in 'aeiou'])

    >>> msg = Value('Hello World!)
    >>> msg | count_vowels() | Sink(print, 'Number of vowels:')
    Number of vowels: 3
    >>> msg.emit('Wahuuu')
    Number of vowels: 4

You can even make configurable ``Map`` s and ``Filter`` s:

.. code-block:: python3

    >>> import re

    >>> @build_filter
    ... def filter_pattern(pattern, s):
    ...     return re.search(pattern, s) is not None

    >>> msg = Value('Cars passed: 135!')
    >>> msg | filter_pattern('[0-9]*') | Sink(print)
    Cars passed: 135!
    >>> msg.emit('No cars have passed')
    >>> msg.emit('Only 1 car has passed')
    Only 1 car has passed


Install
=======

.. code-block:: bash

    pip install broqer

.. marker-for-api

API
===

Publishers
----------

A Publisher_ is the source for messages.

Using ``asyncio`` event loop:

+------------------------------------+--------------------------------------------------------------------------+
| Publisher_ ()                      | Basic publisher                                                          |
+------------------------------------+--------------------------------------------------------------------------+
| StatefulPublisher_ (init)          | Publisher keeping an internal state                                      |
+------------------------------------+--------------------------------------------------------------------------+
| FromPolling_ (interval, func, ...) | Call ``func(*args, **kwargs)`` periodically and emit the returned values |
+------------------------------------+--------------------------------------------------------------------------+

Operators
---------

+-------------------------------------+-----------------------------------------------------------------------------+
| Accumulate_ (func, init)            | Apply ``func(value, state)`` which is returning new state and value to emit |
+-------------------------------------+-----------------------------------------------------------------------------+
| Cache_ (\*init)                     | Caching the emitted values to access it via ``.cache`` property             |
+-------------------------------------+-----------------------------------------------------------------------------+
| CatchException_ (\*exceptions)      | Catching exceptions of following operators in the pipelines                 |
+-------------------------------------+-----------------------------------------------------------------------------+
| CombineLatest_ (\*publishers)       | Combine the latest emit of multiple publishers and emit the combination     |
+-------------------------------------+-----------------------------------------------------------------------------+
| Filter_ (predicate, ...)            | Filters values based on a ``predicate`` function                            |
+-------------------------------------+-----------------------------------------------------------------------------+
| Map_ (map_func, \*args, \*\*kwargs) | Apply ``map_func(*args, value, **kwargs)`` to each emitted value            |
+-------------------------------------+-----------------------------------------------------------------------------+
| Merge_ (\*publishers)               | Merge emits of multiple publishers into one stream                          |
+-------------------------------------+-----------------------------------------------------------------------------+
| Partition_ (size)                   | Group ``size`` emits into one emit as tuple                                 |
+-------------------------------------+-----------------------------------------------------------------------------+
| Reduce_ (func, init)                | Apply ``func`` to the current emitted value and the last result of ``func`` |
+-------------------------------------+-----------------------------------------------------------------------------+
| Replace_ (value)                    | Replace each received value by the given value                              |
+-------------------------------------+-----------------------------------------------------------------------------+
| SlidingWindow_ (size, ...)          | Group ``size`` emitted values overlapping                                   |
+-------------------------------------+-----------------------------------------------------------------------------+
| Switch_ (mapping)                   | Emit selected source mapped by ``mapping``                                  |
+-------------------------------------+-----------------------------------------------------------------------------+

Using ``asyncio`` event loop:

+-------------------------------------+-------------------------------------------------------------------------+
| Debounce_ (duetime, \*reset_value)  | Emit a value only after a given idle time (emits meanwhile are skipped) |
+-------------------------------------+-------------------------------------------------------------------------+
| Delay_ (delay)                      | Emit every value delayed by the given time                              |
+-------------------------------------+-------------------------------------------------------------------------+
| MapAsync_ (map_coro, mode, ...)     | Apply ``map_coro`` to each emitted value allowing async processing      |
+-------------------------------------+-------------------------------------------------------------------------+
| MapThreaded_ (map_func, mode, ...)  | Apply ``map_func`` to each emitted value allowing threaded processing   |
+-------------------------------------+-------------------------------------------------------------------------+
| Sample_ (interval)                  | Emit the last received value periodically                               |
+-------------------------------------+-------------------------------------------------------------------------+
| Throttle_ (duration)                | Rate limit emits by the given time                                      |
+-------------------------------------+-------------------------------------------------------------------------+

Subscribers
-----------

A Subscriber_ is the sink for messages.

+----------------------------------+--------------------------------------------------------------+
| Sink_ (func, \*args, \*\*kwargs) | Apply ``func(*args, value, **kwargs)`` to each emitted value |
+----------------------------------+--------------------------------------------------------------+
| OnEmitFuture_ (timeout=None)     | Build a future able to await for                             |
+----------------------------------+--------------------------------------------------------------+
| hub.utils.TopicMapper_ (d)       | Update a dictionary with changes from topics                 |
+----------------------------------+--------------------------------------------------------------+
| Trace_ (d)                       | Debug output for publishers                                  |
+----------------------------------+--------------------------------------------------------------+

Subjects
--------

+--------------------------+--------------------------------------------------------------+
| Subject_ ()              | Source with ``.emit(*args)`` method to publish a new message |
+--------------------------+--------------------------------------------------------------+
| Value_ (\*init)          | Source with a state (initialized via ``init``)               |
+--------------------------+--------------------------------------------------------------+

.. _Subject: https://github.com/semiversus/python-broqer/blob/master/broqer/subject.py
.. _Value: https://github.com/semiversus/python-broqer/blob/master/broqer/subject.py
.. _Publisher: https://github.com/semiversus/python-broqer/blob/master/broqer/publisher.py
.. _StatefulPublisher: https://github.com/semiversus/python-broqer/blob/master/broqer/publisher.py
.. _Subscriber: https://github.com/semiversus/python-broqer/blob/master/broqer/subscriber.py
.. _Accumulate: https://github.com/semiversus/python-broqer/blob/master/broqer/op/accumulate.py
.. _Cache: https://github.com/semiversus/python-broqer/blob/master/broqer/op/cache.py
.. _CatchException: https://github.com/semiversus/python-broqer/blob/master/broqer/op/catch_exception.py
.. _CombineLatest: https://github.com/semiversus/python-broqer/blob/master/broqer/op/combine_latest.py
.. _Debounce: https://github.com/semiversus/python-broqer/blob/master/broqer/op/debounce.py
.. _Delay: https://github.com/semiversus/python-broqer/blob/master/broqer/op/delay.py
.. _Filter: https://github.com/semiversus/python-broqer/blob/master/broqer/op/filter_.py
.. _FromPolling: https://github.com/semiversus/python-broqer/blob/master/broqer/op/publishers/from_polling.py
.. _MapAsync: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map_async.py
.. _MapThreaded: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map_threaded.py
.. _Map: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map_.py
.. _Merge: https://github.com/semiversus/python-broqer/blob/master/broqer/op/merge.py
.. _Partition: https://github.com/semiversus/python-broqer/blob/master/broqer/op/partition.py
.. _Reduce: https://github.com/semiversus/python-broqer/blob/master/broqer/op/reduce.py
.. _Replace: https://github.com/semiversus/python-broqer/blob/master/broqer/op/replace.py
.. _Sample: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sample.py
.. _Sink: https://github.com/semiversus/python-broqer/blob/master/broqer/op/subscribers/sink.py
.. _SlidingWindow: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sliding_window.py
.. _Switch: https://github.com/semiversus/python-broqer/blob/master/broqer/op/switch.py
.. _Throttle: https://github.com/semiversus/python-broqer/blob/master/broqer/op/throttle.py
.. _OnEmitFuture: https://github.com/semiversus/python-broqer/blob/master/broqer/op/subscribers/on_emit_future.py
.. _Trace: https://github.com/semiversus/python-broqer/blob/master/broqer/op/subscribers/trace.py
.. _hub.utils.TopicMapper: https://github.com/semiversus/python-broqer/blob/master/broqer/hub/utils/topic_mapper.py

Credits
=======

Broqer was inspired by:

* RxPY_: Reactive Extension for Python (by Børge Lanes and Dag Brattli)
* aioreactive_: Async/Await reactive tools for Python (by Dag Brattli)
* streamz_: build pipelines to manage continuous streams of data (by Matthew Rocklin)
* MQTT_: M2M connectivity protocol
* Florian Feurstein: spending hours of discussion, coming up with great ideas and help me understand the concepts!

.. _RxPY: https://github.com/ReactiveX/RxPY
.. _aioreactive: https://github.com/dbrattli/aioreactive
.. _streamz: https://github.com/mrocklin/streamz
.. _MQTT: http://mqtt.org/
