# How to use
See examples for usage

# Naming
* Broker/Hub/Dispatcher
* Publisher/Server/Oberservable/Emitter
* Subscriber/Client/Observer/Sink
* Topic/Channel/Stream/Signal
* subscribe/register/connect

# Clues
* `stream.meta` can be cached and populated afterwards, as it stays the same dict
* `_subscription_callback` is removed - inherit from Stream and overload `subscribe`

# Discussion
* should meta dict be part of AssignedStream?
* configurator could use root hub and search for streams marked as CONFIG in their metadata
* define protocol for TCP socket to hub - subscribe, emit
