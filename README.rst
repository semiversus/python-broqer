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

.. header

Synopsis
========

- Pure python implementation without dependencies
- Under MIT license (2018 Günther Jena)
- Source is hosted on GitHub.com_
- Documentation is hosted on ReadTheDocs.com_
- Tested on Python 3.5, 3.6, 3.7 and 3.8
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
.. _Hub: https://python-broqer.readthedocs.io/en/latest/hub.html

Showcase
========

In other frameworks a *Publisher* is sometimes called *Oberservable*. A *Subscriber*
is able to observe changes the publisher is emitting. With these basics you're
able to use the observer pattern - let's see!

Observer pattern
----------------

Subscribing to a publisher is done via the .subscribe() method.
A simple subscriber is ``op.Sink`` which is calling a function with optional positional
and keyword arguments.

.. code-block:: python3

    >>> from broqer import Value, op
    >>> a = Value(5)  # create a value (publisher and subscriber with state)
    >>> disposable = a.subscribe(op.Sink(print, 'Change:'))  # subscribe a callback
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
    >>> c.subscribe(op.Sink(print, 'c:'))
    c: False

    >>> a.emit(2)
    c: True

    >>> b.emit(10)
    c: False

Also fancy stuff like getting item by index or key is possible:

.. code-block:: python3

    >>> i = Value('a')
    >>> d = Value({'a':100, 'b':200, 'c':300})

    >>> d[i].subscribe(op.Sink(print, 'r:'))
    r: 100

    >>> i.emit('c')
    r: 300
    >>> d.emit({'c':123})
    r: 123

Some python built in functions can't return Publishers (e.g. ``len()`` needs to
return an integer). For this cases special functions are defined in broqer: ``Str``,
``Int``, ``Float``, ``Len`` and ``In`` (for ``x in y``). Also other functions
for convenience are available: ``All``, ``Any``, ``BitwiseAnd`` and ``BitwiseOr``.

Attribute access on a publisher is building a publisher where the actual attribute
access is done on emitting values. A publisher has to know, which type it should
mimic - this is done via ``.inherit_type(type)``.

.. code-block:: python3

    >>> i = Value('Attribute access made REACTIVE')
    >>> i.inherit_type(str)
    >>> i.lower().split(sep=' ') | op.Sink(print)
    ['attribute', 'access', 'made', 'reactive']

    >>> i.emit('Reactive and pythonic')
    ['reactive', 'and', 'pythonic']

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
    >>> (msg | count_vowels).subscribe(op.Sink(print, 'Number of vowels:'))
    Number of vowels: 3
    >>> msg.emit('Wahuuu')
    Number of vowels: 4

You can even make configurable ``Map`` s and ``Filter`` s:

.. code-block:: python3

    >>> import re

    >>> @build_filter_factory
    ... def filter_pattern(pattern, s):
    ...     return re.search(pattern, s) is not None

    >>> msg = Value('Cars passed: 135!')
    >>> (msg | filter_pattern('[0-9]*')).subscribe(op.Sink(print))
    Cars passed: 135!
    >>> msg.emit('No cars have passed')
    >>> msg.emit('Only 1 car has passed')
    Only 1 car has passed


Install
=======

.. code-block:: bash

    pip install broqer

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
.. _Value: https://python-broqer.readthedocs.io/en/latest/subjects.html#value
.. _Publisher: https://python-broqer.readthedocs.io/en/latest/publishers.html#publisher
.. _Subscriber: https://python-broqer.readthedocs.io/en/latest/subscribers.html#subscriber
.. _CombineLatest: https://python-broqer.readthedocs.io/en/latest/operators/combine_latest.py
.. _Filter: https://python-broqer.readthedocs.io/en/latest/operators/filter_.py
.. _Map: https://python-broqer.readthedocs.io/en/latest/operators/map_.py
.. _Sink: https://python-broqer.readthedocs.io/en/latest/operators/subscribers/sink.py
.. _OnEmitFuture: https://python-broqer.readthedocs.io/en/latest/subscribers.html#trace
.. _Trace: https://python-broqer.readthedocs.io/en/latest/subscribers.html#trace

.. api

API
===

Publishers
----------

A Publisher_ is the source for messages.

+------------------------------------+--------------------------------------------------------------------------+
| Publisher_ ()                      | Basic publisher                                                          |
+------------------------------------+--------------------------------------------------------------------------+

Operators
---------

+-------------------------------------+-----------------------------------------------------------------------------+
| CombineLatest_ (\*publishers)       | Combine the latest emit of multiple publishers and emit the combination     |
+-------------------------------------+-----------------------------------------------------------------------------+
| Filter_ (predicate, ...)            | Filters values based on a ``predicate`` function                            |
+-------------------------------------+-----------------------------------------------------------------------------+
| Map_ (map_func, \*args, \*\*kwargs) | Apply ``map_func(*args, value, **kwargs)`` to each emitted value            |
+-------------------------------------+-----------------------------------------------------------------------------+

Subscribers
-----------

A Subscriber_ is the sink for messages.

+----------------------------------+--------------------------------------------------------------+
| Sink_ (func, \*args, \*\*kwargs) | Apply ``func(*args, value, **kwargs)`` to each emitted value |
+----------------------------------+--------------------------------------------------------------+
| OnEmitFuture_ (timeout=None)     | Build a future able to await for                             |
+----------------------------------+--------------------------------------------------------------+
| Trace_ (d)                       | Debug output for publishers                                  |
+----------------------------------+--------------------------------------------------------------+

Values
--------

+--------------------------+--------------------------------------------------------------+
| Value_ (\*init)          | Publisher and Subscriber                                     |
+--------------------------+--------------------------------------------------------------+
