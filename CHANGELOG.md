## 2.3.1

* fix OnEmitFuture behavior when using `omit_subscription` argument

## 2.3.0

* added `Cache` operator

## 2.2.0

* added `Throttle` operator (thanks to `flofeurstein <https://github.com/flofeurstein>`_ )

## 2.1.0

* .reset_state is now calling .reset_state for all subscribers

## 2.0.3

* prevent iteration over a publisher
* fix another bug in BitwiseCombineLatest (emitted NONE when no publisher had state)

## 2.0.2

* fixed behaviour for BitwiseCombineLatest when a Publisher has state NONE

## 2.0.1

* fixed problem in `Publisher.register_on_subscription_callback()` when subscriptions already are available

## 2.0.0

* replace bumpversion by use_scm_version
* replace pylint by pylama
* fixed `Publisher.notify` bug (39d17642610ff86c9264986788e929419f007803)
* added `BitwiseCombineLatest` and `map_bit` operator
* added `Not` operator
* remove Pipfile functionality

## 2.0.0rc1

* rename `default_error_handler.py` to `error_handler.py`
* added `BitwiseCombineLatest` and `map_bit`
* fixing typing warnings