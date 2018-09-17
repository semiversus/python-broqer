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

- Pure python implementation without dependencies
- Under MIT license (2018 Günther Jena)
- Source is hosted on GitHub.com_
- Documentation is hosted on ReadTheDocs.com_
- Tested on Python 3.5, 3.6 and 3.7
- Compact library (<1000 lines of code) and well documented (>1000 lines of comments)
- Fully unit tested with pytest_, coding style checked with flake8_, static type checked with mypy_, static code checked with pylint_
- Operators known from ReactiveX_ and other streaming frameworks (like distinct_, combine_latest_, ...)
- Supporting ``asyncio`` for time depended operations and using coroutines (e.g. map_async_, debounce_, ...)
- Publishers are *awaitable* (e.g. ``await adc_raw``)
- Broker functionality via Hub_

  + Centralised object to keep track of publishers and subscribers
  + Starting point to build applications with a microservice architecture

.. _pytest: https://docs.pytest.org/en/latest
.. _flake8: http://flake8.pycqa.org/en/latest/
.. _mypy: http://mypy-lang.org/
.. _pylint: https://www.pylint.org/
.. _GitHub.com: https://github.com/semiversus/python-broqer
.. _ReadTheDocs.com: http://python-broqer.readthedocs.io
.. _ReactiveX: http://reactivex.io/

.. _Hub: https://github.com/semiversus/python-broqer/blob/master/broqer/hub.py
.. _debounce: https://github.com/semiversus/python-broqer/blob/master/broqer/op/debounce.py
.. _map_async: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map_async.py
.. _combine_latest: https://github.com/semiversus/python-broqer/blob/master/broqer/op/combine_latest.py
.. _distinct: https://github.com/semiversus/python-broqer/blob/master/broqer/op/distinct.py

.. marker-for-example

Showcase
========

In other frameworks Publisher_ are sometimes called ``Oberservable``. A subscriber
is able to observe changes the publisher is emitting.

Observer pattern
----------------

.. code-block:: python

    >>> from broqer import Value, op
    >>> a = Value(5)  # create a value (publisher and subscriber with state)
    >>> disposable = a | op.Sink(print, 'Change:')  # subscribe a callback
    Change: 5

    >>> a.emit(3)  # change the value
    Change: 3

    >>> disposable.dispose()  # unsubscribe

Combining publishers
--------------------

.. code-block:: python

    >>> from broqer import Value, op
    >>> a = Value(1)
    >>> b = Value(3)

    >>> c = a * 3 > b  # create a new publisher via operator overloading
    >>> c | op.Sink(print, 'c =')
    c = False

    >>> a.emit(1)  # will not change the state of c
    >>> a.emit(2)
    c = True


Install
=======

.. code-block:: bash

    pip install broqer

.. marker-for-api

How it works
============

Basically it's based on the observable pattern - an object you can register on and you will be informed as
soon the state has changed. The observable are called ``Publishers``.

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
| partition_ (size)                   | Group ``size`` emits into one emit as tuple                                 |
+-------------------------------------+-----------------------------------------------------------------------------+
| reduce_ (func, init)                | Apply ``func`` to the current emitted value and the last result of ``func`` |
+-------------------------------------+-----------------------------------------------------------------------------+
| sliding_window_ (size, ...)         | Group ``size`` emitted values overlapping                                   |
+-------------------------------------+-----------------------------------------------------------------------------+
| switch_ (mapping)                   | Emit selected source mapped by ``mapping``                                  |
+-------------------------------------+-----------------------------------------------------------------------------+

Using ``asyncio`` event loop:

+-------------------------------------+-------------------------------------------------------------------------+
| debounce_ (duetime, \*reset_value)  | Emit a value only after a given idle time (emits meanwhile are skipped) |
+-------------------------------------+-------------------------------------------------------------------------+
| delay_ (delay)                      | Emit every value delayed by the given time                              |
+-------------------------------------+-------------------------------------------------------------------------+
| map_async_ (map_coro, mode, ...)    | Apply ``map_coro`` to each emitted value allowing async processing      |
+-------------------------------------+-------------------------------------------------------------------------+
| map_threaded_ (map_func, mode, ...) | Apply ``map_func`` to each emitted value allowing threaded processing   |
+-------------------------------------+-------------------------------------------------------------------------+
| sample_ (interval)                  | Emit the last received value periodically                               |
+-------------------------------------+-------------------------------------------------------------------------+
| throttle_ (duration)                | Rate limit emits by the given time                                      |
+-------------------------------------+-------------------------------------------------------------------------+

Subscribers
-----------

A Subscriber_ is the sink for messages.

+----------------------------------+--------------------------------------------------------------+
| Sink_ (func, \*args, \*\*kwargs) | Apply ``func(*args, value, **kwargs)`` to each emitted value |
+----------------------------------+--------------------------------------------------------------+
| OnEmitFuture_ (timeout=None)     | Build a future able to await for                             |
+----------------------------------+--------------------------------------------------------------+
| TopicMapper_ (d)                 | Update a dictionary with changes from topics                 |
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
.. _Publisher: https://github.com/semiversus/python-broqer/blob/master/broqer/core.py
.. _StatefulPublisher: https://github.com/semiversus/python-broqer/blob/master/broqer/core.py
.. _Subscriber: https://github.com/semiversus/python-broqer/blob/master/broqer/core.py
.. _accumulate: https://github.com/semiversus/python-broqer/blob/master/broqer/op/accumulate.py
.. _cache: https://github.com/semiversus/python-broqer/blob/master/broqer/op/cache.py
.. _catch_exception: https://github.com/semiversus/python-broqer/blob/master/broqer/op/catch_exception.py
.. _delay: https://github.com/semiversus/python-broqer/blob/master/broqer/op/delay.py
.. _filter: https://github.com/semiversus/python-broqer/blob/master/broqer/op/filter.py
.. _FromPolling: https://github.com/semiversus/python-broqer/blob/master/broqer/op/from_polling.py
.. _map_threaded: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map_threaded.py
.. _map: https://github.com/semiversus/python-broqer/blob/master/broqer/op/map.py
.. _merge: https://github.com/semiversus/python-broqer/blob/master/broqer/op/merge.py
.. _partition: https://github.com/semiversus/python-broqer/blob/master/broqer/op/partition.py
.. _reduce: https://github.com/semiversus/python-broqer/blob/master/broqer/op/reduce.py
.. _sample: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sample.py
.. _Sink: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sink.py
.. _sliding_window: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sliding_window.py
.. _switch: https://github.com/semiversus/python-broqer/blob/master/broqer/op/switch.py
.. _throttle: https://github.com/semiversus/python-broqer/blob/master/broqer/op/throttle.py
.. _OnEmitFuture: https://github.com/semiversus/python-broqer/blob/master/broqer/op/emit_future.py
.. _Trace: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sink/trace.py
.. _TopicMapper: https://github.com/semiversus/python-broqer/blob/master/broqer/op/sink/topic_mapper.py

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
