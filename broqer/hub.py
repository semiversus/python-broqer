"""
>>> from broqer import Hub, Value, op
>>> hub = Hub()

The hub is handling with topics referencing to publishers or subjects:

>>> value1 = hub['value1']

Each following access will return the same object

>>> value1 is hub['value1']
True

It's possible to subscribe to a topic

>>> _d1 = hub['value1'] | op.sink(print, 'Output:')

At the moment this hub object is not assigned to a publisher

>>> hub['value1'].assigned
False

Checking if a topic already exists is done via ``in`` operator

>>> 'value1' in hub
True
>>> 'value2' in hub
False

It will store the first .emit for an unassigned topic:
>>> hub['value1'].emit(2)

And will raise an exception if .emit is used a second time on unassigned topic:

>>> hub['value1'].emit(3)
Traceback (most recent call last):
...
broqer.core.publisher.SubscriptionError: Only one emit will be stored ...

Assign a publisher to a hub topic:

>>> _ = hub.assign('value1', Value(1))
Output: 1
Output: 2
>>> hub['value1'].assigned
True

>>> _d1.dispose()

Also assigning publisher first and then subscribing is possible:

>>> _ = hub.assign('value2', Value(2))
>>> _d2 = hub['value2'] | op.sink(print, 'Output:')
Output: 2

>>> hub['value2'].emit(3)
Output: 3

>>> _d2.dispose()

It's not possible to assign a second publisher to a hub topic:

>>> _ = hub.assign('value2', Value(0))
Traceback (most recent call last):
...
broqer.core.publisher.SubscriptionError: Topic is already assigned

Meta data
---------

Another feature is defining meta data as dictionary to a hub topic:

>>> _ = hub.assign('value3', Value(0), meta={'maximum':10})
>>> hub['value3'].meta
{'maximum': 10}

Wait for assignment
-------------------

It's also possible to wait for an assignment:

>>> import asyncio

>>> _f2 = asyncio.ensure_future(hub['value4'].wait_for_assignment())
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
>>> _f2.done()
False

>>> _ = hub.assign('value4', Value(0))
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
>>> _f2.done()
True

When already assigned it will not wait at all:

>>> _f2 = asyncio.ensure_future(hub['value4'].wait_for_assignment())
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
>>> _f2.done()
True
"""
import asyncio
from collections import OrderedDict
from types import MappingProxyType
from typing import Any, Optional, Dict  # noqa: F401

from broqer import (Publisher, Subscriber, SubscriptionDisposable,
                    SubscriptionError, UNINITIALIZED)


class Topic(Publisher, Subscriber):
    def __init__(self, hub: 'Hub', path: str) -> None:
        Publisher.__init__(self)
        self._subject = None  # type: Publisher
        self._path = path
        self.assignment_future = None
        self._pre_assign_emit = UNINITIALIZED  # type: Any

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool=False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if self._subject is not None:
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
        except AttributeError:  # if self._subject is None
            raise ValueError('Topic is not yet assigned')

    def emit(self, value: Any,
             who: Optional[Publisher] = None) -> asyncio.Future:
        if self._subject is None:
            if self._pre_assign_emit is not UNINITIALIZED:
                # method will be replaced by .__call__
                raise SubscriptionError('Only one emit will be stored before' +
                                        ' assignment')
            self._pre_assign_emit = value
            return None

        if who is self._subject:
            return self.notify(value)

        assert isinstance(self._subject, Subscriber), \
            'Topic has to be a subscriber'

        return self._subject.emit(value, who=self)

    def assign(self, subject):
        assert isinstance(subject, (Publisher, Subscriber))

        if self._subject is not None:
            raise SubscriptionError('Topic is already assigned')
        self._subject = subject
        if self._subscriptions:
            self._subject.subscribe(self)
        if self._pre_assign_emit is not UNINITIALIZED:
            self._subject.emit(self._pre_assign_emit, who=self)
        if self.assignment_future is not None:
            self.assignment_future.set_result(None)

    def freeze(self):
        if self._subject is None:
            raise ValueError('Topic %r is not assigned' % self._path)

    @property
    def assigned(self):
        return self._subject is not None

    @property
    def subject(self):
        return self._subject

    async def wait_for_assignment(self):
        if not self.assigned:
            self.assignment_future = asyncio.get_event_loop().create_future()
            await self.assignment_future

    @property
    def path(self) -> str:
        return self._path


class MetaTopic(Topic):
    def __init__(self, hub: 'Hub', path: str) -> None:
        Topic.__init__(self, hub, path)
        self._meta = dict()  # type: Dict[str, Any]

    def assign(self, subject, meta=None):
        Topic.assign(self, subject)
        if meta is not None:
            self._meta.update(meta)

    @property
    def meta(self):
        return self._meta


class Hub:
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

    def __setitem__(self, path: str, publisher: Publisher):
        if not isinstance(publisher, (Publisher, Subscriber)):
            raise TypeError('Assigned topic has to be publisher or subscriber')
        self.assign(path, publisher)

    def __contains__(self, path: str) -> bool:
        return path in self._topics

    def __iter__(self):
        return sorted(self._topics.keys()).__iter__()

    def freeze(self, freeze: bool = True):
        for topic in self._topics.values():
            topic.freeze()
        self._frozen = freeze

    @property
    def topics(self):
        topics_sorted = sorted(self._topics.items(), key=lambda t: t[0])
        return MappingProxyType(OrderedDict(topics_sorted))

    @property
    def topic_factory(self):
        return self._topic_factory

    def assign(self, topic_str: str, publisher: Publisher,
               *args, **kwargs) -> Topic:

        topic = self[topic_str]
        topic.assign(publisher, *args, **kwargs)  # type: ignore
        return topic


class SubHub:
    def __init__(self, hub: Hub, prefix: str) -> None:
        self._hub = hub
        assert not prefix.endswith('.'), 'Prefix should not end with \'.\''
        assert prefix, 'Prefix should not be empty'
        self._prefix = prefix + '.'

    def __getitem__(self, topic: str) -> Topic:
        return self._hub[self._prefix + topic]

    def assign(self, topic_str: str, publisher: Publisher,
               *args, **kwargs) -> Topic:

        return self._hub.assign(self._prefix + topic_str, publisher,
                                *args, **kwargs)
