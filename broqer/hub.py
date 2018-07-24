"""
>>> from broqer import Hub, Value, op
>>> hub = Hub()

The hub is handling with topics referencing to publishers or subjects:

>>> value1 = hub['value1']

Each following access will return the same object

>>> value1 == hub['value1']
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

It will raise an exception if .emit is used on an unassigned topic:

>>> hub['value1'].emit(1)
Traceback (most recent call last):
...
broqer.core.SubscriptionError: No subject is assigned to this Topic

Assign a publisher to a hub topic:

>>> _ = hub.assign('value1', op.Just(1))
Output: 1
>>> hub['value1'].assigned
True

Assigning to a hub topic without .publish will fail:

>>> _ = op.Just(1) | hub['value2']
Traceback (most recent call last):
...
broqer.core.SubscriptionError: ...

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
broqer.core.SubscriptionError: Topic is already assigned

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
>>> _f1 = asyncio.ensure_future(hub['value4'].wait_for_assignment(0.01))
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
>>> _f1.exception()
TimeoutError()

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
                    SubscriptionError)


class Topic(Publisher, Subscriber):
    def __init__(self, path: str) -> None:
        Publisher.__init__(self)
        self._subject = None  # type: Publisher
        self._path = path
        self._meta = dict()  # type: Dict[str, Any]
        self.assignment_future = None

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)

        if len(self._subscriptions) == 1 and self._subject is not None:
            self._subject.subscribe(self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions and self._subject is not None:
            self._subject.unsubscribe(self)

    def get(self):
        return self._subject.get()

    def emit(self, *args: Any, who: Optional[Publisher] = None) -> None:
        if self._subject is None:
            # method will be replaced by .__call__
            raise SubscriptionError('No subject is assigned to this Topic')

        if who == self._subject:
            self.notify(*args)
            return None

        assert isinstance(self._subject, Subscriber), \
            'Topic has to be a subscriber'

        return self._subject.emit(*args, who=self)

    def __call__(self, *args, **kwargs) -> None:
        raise SubscriptionError(
            'To assign a publisher to this topic use "hub.assign(publisher, ' +
            'topic, [meta])" instead.')

    def assign(self, subject, meta):
        if self._subject is not None:
            raise SubscriptionError('Topic is already assigned')
        self._subject = subject
        if meta:
            self._meta.update(meta)

    @property
    def assigned(self):
        return self._subject is not None

    @property
    def subject(self):
        return self._subject

    async def wait_for_assignment(self, timeout=None):
        if not self.assigned:
            self.assignment_future = asyncio.get_event_loop().create_future()
            if timeout is None:
                await self.assignment_future
            else:
                await asyncio.wait_for(
                    asyncio.shield(self.assignment_future), timeout)

    @property
    def meta(self) -> dict:
        return self._meta

    @property
    def path(self) -> str:
        return self._path


class Hub:
    _topic_cls = Topic

    def __init__(self, permitted_meta_keys=None):
        self._topics = dict()
        if permitted_meta_keys is not None:
            self._permitted_meta_keys = set(permitted_meta_keys)
        else:
            self._permitted_meta_keys = None

    def __getitem__(self, path: str) -> Topic:
        try:
            return self._topics[path]
        except KeyError:
            topic = self._topic_cls(path)
            self._topics[path] = topic
            return topic

    def __contains__(self, path: str) -> bool:
        return path in self._topics

    def __iter__(self):
        return sorted(self._topics.keys()).__iter__()

    @property
    def topics(self):
        topics_sorted = sorted(self._topics.items(), key=lambda t: t[0])
        return MappingProxyType(OrderedDict(topics_sorted))

    @property
    def unassigned_topics(self):
        topics_sorted = sorted(self._topics.items(), key=lambda t: t[0])
        result_topics = ((n, t) for n, t in topics_sorted if not t.assigned)
        return MappingProxyType(OrderedDict(result_topics))

    def assign(self, topic_str: str, publisher: Publisher,
               meta: Optional[dict] = None) -> Topic:

        topic = self[topic_str]

        if meta and self._permitted_meta_keys:
            non_keys = set(meta.keys()) - self._permitted_meta_keys
            if non_keys:
                raise KeyError('Not permitted meta keys: %r' % non_keys)

        topic.assign(publisher, meta)

        if topic:
            publisher.subscribe(topic)

        if topic.assignment_future:
            topic.assignment_future.set_result(None)

        return topic


class SubHub:
    def __init__(self, hub: Hub, prefix: str) -> None:
        self._hub = hub
        assert not prefix.endswith('.'), 'Prefix should not end with \'.\''
        assert prefix, 'Prefix should not be empty'
        self._prefix = prefix + '.'

    def __getitem__(self, topic: str) -> Topic:
        return self._hub[self._prefix + topic]

    def __contains__(self, topic: str) -> bool:
        return self._prefix + topic in self._hub

    def __iter__(self):
        length = len(self._prefix)
        return (t[length:] for t in self._hub if t.startswith(self._prefix))

    @property
    def topics(self):
        length = len(self._prefix)
        topics = ((n[length:], t) for (n, t) in self._hub.topics.items()
                  if n.startswith(self._prefix))
        return MappingProxyType(OrderedDict(topics))

    @property
    def unassigned_topics(self):
        length = len(self._prefix)
        topics = ((n[length:], t) for (n, t)
                  in self._hub.unassigned_topics.items()
                  if n.startswith(self._prefix))
        return MappingProxyType(OrderedDict(topics))

    def assign(self, topic_str: str, publisher: Publisher,
               meta: Optional[dict] = None) -> Topic:

        return self._hub.assign(self._prefix + topic_str, publisher, meta)
