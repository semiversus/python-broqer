===================
Python Broqer
===================
        
.. image:: https://img.shields.io/github/license/semiversus/python-broqer.svg
        :target: https://en.wikipedia.org/wiki/MIT_License
        
Carefully crafted library to operate with continuous streams of data in a reactive style with publish/subscribe and broker functionality.

Synopsis
========

* Pure python implementation with no dependencies (Python 3.5+)
* Operators known from ReactiveX (like ``distinct``, ``combine_latest``, ...)
* Supporting `asyncio` for time depended operations and using coroutines (e.g. `map_async`)
* Supporting broker functionality
* Under MIT license (2018 Günther Jena)

Installing via

.. code-block:: python

    pip install broqer

API
===

Sources
-------

+---------------+--------------------------------------------------------------+
| Subject_()    | Source with ``.emit(*args)`` method to publish a new message |
+---------------+--------------------------------------------------------------+
| Value_(*init) | Source with a state (initialized via ``init``)               |
+---------------+--------------------------------------------------------------+

Operators
---------

+-------------------------------+-----------------------------------------------------------------------------+
| accumulate_(func, init)       | Apply ``func(value, state)`` which is returning new state and value to emit |
+-------------------------------+-----------------------------------------------------------------------------+
| cache_(*init)                 | Caching the emitted values to access it via ``.cache`` property             |
+-------------------------------+-----------------------------------------------------------------------------+
| catch_exception_(*exceptions) | Catching exceptions of following operators in the pipelines                 |
+-------------------------------+-----------------------------------------------------------------------------+
| combine_latest_(*publishers)  | Combine the latest emit of multiple publishers and emit the combination     |
+-------------------------------+-----------------------------------------------------------------------------+

Sinks
-----

References
==========

Broqer was inspired by:

* RxPY_: Reactive Extension for Python (by Børge Lanes and Dag Brattli)
* aioreactive_: Async/Await reactive tools for Python (by Dag Brattli)
* streamz_: build pipelines to manage continous streams of data (by Matthew Rocklin)
* MQTT_: M2M connectivity protocol
* Florian Feurstein: spending hours of discussion, coming up with great ideas and help me understand the concepts! 

.. _RxPY: https://github.com/ReactiveX/RxPY
.. _aioreactive: https://github.com/dbrattli/aioreactive
.. _streamz: https://github.com/mrocklin/streamz
.. _MQTT: http://mqtt.org/
.. _Subject: https://github.com/semiversus/python-broqer/blob/master/broqer/subject.py
.. _Value: https://github.com/semiversus/python-broqer/blob/master/broqer/subject.py
.. _accumulate: https://github.com/semiversus/python-broqer/blob/master/broqer/op/accumulate.py
.. _cache: https://github.com/semiversus/python-broqer/blob/master/broqer/op/cache.py
.. _catch_exception: https://github.com/semiversus/python-broqer/blob/master/broqer/op/catch_exception.py
.. _combine_latest: https://github.com/semiversus/python-broqer/blob/master/broqer/op/combine_latest.py