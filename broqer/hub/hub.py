"""
>>> from broqer import Hub, Value, op
>>> hub = Hub()

The hub is handling with topics referencing to publishers or subjects:

>>> value1 = hub['value1']

Each following access will return the same object

>>> value1 is hub['value1']
True

It's possible to subscribe to a topic

>>> _d1 = hub['value1'] | op.Sink(print, 'Output:')

At the moment this hub object is not assigned to a publisher

>>> hub['value1'].assigned
False

Checking if a topic already exists is done via ``in`` operator

>>> 'value1' in hub
True
>>> 'value2' in hub
False

It will store each .emit for an unassigned topic:
>>> hub['value1'].emit(2)
>>> hub['value1'].emit(3)

Assign a publisher to a hub topic:

>>> _ = hub['value1'].assign(Value(1))
Output: 1
Output: 2
Output: 3
>>> hub['value1'].assigned
True

>>> _d1.dispose()

Also assigning publisher first and then subscribing is possible:

>>> _ = hub['value2'].assign(Value(2))
>>> _d2 = hub['value2'] | op.Sink(print, 'Output:')
Output: 2

>>> hub['value2'].emit(3)
Output: 3

>>> _d2.dispose()

It's not possible to assign a second publisher to a hub topic:

>>> _ = hub['value2'].assign(Value(0))
Traceback (most recent call last):
...
broqer.publisher.SubscriptionError: Topic 'value2' already assigned

Meta data
---------

Another feature is defining meta data as dictionary to a hub topic:

>>> _ = hub['value3'].assign(Value(0), meta={'maximum':10})
>>> hub['value3'].meta
{'maximum': 10}
"""
import asyncio
from collections import OrderedDict
from types import MappingProxyType
from typing import Any, Optional, Dict  # noqa: F401

from broqer import (Publisher, Subscriber, SubscriptionDisposable,
                    SubscriptionError)


class Topic(Publisher, Subscriber):
    """ Topic acts as a proxy to publishers and/or subscribers. It's used
    in the context of a hub.
    :param hub: reference to the hub
    :param path: the path to this topic (used as key when accessing the hub)
    """
    def __init__(self, hub: 'Hub',  # pylint: disable=unused-argument
                 path: str) -> None:
        Publisher.__init__(self)
        self._subject = None  # type: Publisher
        self._path = path
        self._hub = hub
        self._pre_assign_emit = None  # type: list

    def subscribe(self, subscriber: Subscriber,
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if self._subject is not None:
            assert isinstance(self, Publisher), 'Topic %r has to be a ' \
                'Publisher when using .subscribe()' % self._path

            if len(self._subscriptions) == 1:
                self._subject.subscribe(self)
            else:
                try:
                    value = self._subject.get()
                except ValueError:
                    pass
                else:
                    subscriber.emit(value, who=self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions and self._subject is not None:
            self._subject.unsubscribe(self)

    def get(self):
        try:
            return self._subject.get()
        except AttributeError:  # if self._subject is None or not a Publisher
            raise ValueError('Topic %r is not yet assigned or is not a '
                             'Publisher' % self._path)

    def emit(self, value: Any,
             who: Optional[Publisher] = None) -> asyncio.Future:

        if self._subject is None:
            # if yet unassigned store the emit for later replay
            if self._pre_assign_emit is None:
                self._pre_assign_emit = []
            self._pre_assign_emit.append(value)
            return None

        # notify all subscribers when the source of the .emit is the subject
        if who is self._subject:
            return self.notify(value)

        assert isinstance(self._subject, Subscriber), \
            'Topic %r has to be a Subscriber when using .emit()' % self._path

        # otherwise pass this .emit to the subject
        return self._subject.emit(value, who=self)

    def assign(self, subject):
        """ Assigns the given subject to the topic """
        assert isinstance(subject, (Publisher, Subscriber))

        # check if not already assigned
        if self._subject is not None:
            raise SubscriptionError('Topic %r already assigned' % self._path)

        self._subject = subject

        # subscribe to subject if topic has subscriptions
        if self._subscriptions:
            self._subject.subscribe(self)

        # if topic received emits before assignment replay those emits
        if self._pre_assign_emit is not None:
            for value in self._pre_assign_emit:
                self._subject.emit(value, who=self)
            self._pre_assign_emit = None

        return subject

    def freeze(self):
        """ Called by hub when hub is going to be frozen """
        if self._subject is None:
            raise ValueError('Topic %r is not assigned' % self._path)

    @property
    def assigned(self) -> bool:
        """ Telling as boolean if topic is assigned with a publisher/subscriber
        """
        return self._subject is not None

    @property
    def subject(self):
        """ The assigned subject """
        return self._subject

    @property
    def path(self) -> str:
        """ Topic path used as key in the hub """
        return self._path

    @property
    def hub(self) -> 'Hub':
        """ Reference to hub """
        return self._hub

    def __repr__(self):
        return 'Topic(%r)' % self._path


class MetaTopic(Topic):
    """ MetaTopic is adding a meta dictionary to each topic """
    def __init__(self, hub: 'Hub', path: str) -> None:
        Topic.__init__(self, hub, path)
        self._meta = dict()  # type: Dict[str, Any]

    def assign(self, subject, meta=None):  # pylint: disable=arguments-differ
        Topic.assign(self, subject)
        if meta is not None:
            self._meta.update(meta)

    @property
    def meta(self):
        """ The meta dictionary """
        return self._meta


class Hub:
    """ Hub is a collection of topics where each topic can be referenced as
    string (so called "path").

    :param topic_factory: function used to create new topic objects
    """
    def __init__(self, topic_factory=MetaTopic):
        self._topics = dict()
        self._frozen = False
        self._topic_factory = topic_factory

    def __getitem__(self, path: str) -> Topic:
        try:
            return self._topics[path]
        except KeyError:
            if self._frozen:
                raise ValueError('Hub is frozen, so it\'s impossible to ' +
                                 'access the unknown topic %s' % path)
            topic = self._topic_factory(self, path)
            self._topics[path] = topic
            return topic

    def __contains__(self, path: str) -> bool:
        return path in self._topics

    def __iter__(self):
        return sorted(self._topics.keys()).__iter__()

    def freeze(self, freeze: bool = True):
        """ Freezing the hub means that each topic has to be assigned and no
        new topics can be created after this point.
        """
        for topic in self._topics.values():
            topic.freeze()
        self._frozen = freeze

    @property
    def topics(self):
        """ Ordered dictionary with path:topic ordered by path """
        topics_sorted = sorted(self._topics.items(), key=lambda t: t[0])
        return MappingProxyType(OrderedDict(topics_sorted))

    @property
    def topic_factory(self):
        """ Used topic_factory """
        return self._topic_factory


class SubHub:  # pylint: disable=too-few-public-methods
    """ SubHub is adding a prefix to each topic access """
    def __init__(self, hub: Hub, prefix: str) -> None:
        self._hub = hub
        assert not prefix.endswith('.'), 'Prefix should not end with \'.\''
        assert prefix, 'Prefix should not be empty'
        self._prefix = prefix + '.'

    def __getitem__(self, topic: str) -> Topic:
        return self._hub[self._prefix + topic]

    @property
    def prefix(self):
        """ the prefix of this sub hub """
        return self._prefix[:-1]
