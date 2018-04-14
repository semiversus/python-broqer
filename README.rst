===================
Python Broqer
===================
        
.. image:: https://img.shields.io/github/license/semiversus/python-broqer.svg
        :target: https://en.wikipedia.org/wiki/MIT_License
        
Carefully crafted library to operate with continuous streams of data in a reactive style with publish/subscribe and broker functionality.

Features
========

* Supporting `asyncio` for time depended operations and using coroutines (e.g. `map_async`)
* Operators known from ReactiveX (like `distinct`, `combine_latest`, ...)
* Support type hints and static type checking
* Pure python implementation
* Supporting broker functionality with integrated server

Inspired by:

* RxPY_: Reactive Extension for Python
* aioreactive_: Async/Await reactive tools for Python (by Dag Brattli)
* streamz_: build pipelines to manage continous streams of data (by Matthew Rocklin)
* MQTT_: M2M connectivity protocol
* Florian Feurstein: spending hours of discussion, coming up with great ideas and help me understand the concepts! 


.. _RxPY: https://github.com/ReactiveX/RxPY
.. _aioreactive: https://github.com/dbrattli/aioreactive
.. _streamz: https://github.com/mrocklin/streamz
.. _MQTT: http://mqtt.org/