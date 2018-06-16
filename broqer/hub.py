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
TypeError: No subject is assigned to this Topic

Assign a publisher to a hub topic:

>>> _ = hub.assign('value1', op.Just(1))
Output: 1
>>> hub['value1'].assigned
True

Assigning to a hub topic without .publish will fail:

>>> _ = op.Just(1) | hub['value2']
Traceback (most recent call last):
...
TypeError: Topic is not callable (for use with | operator). ...

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
ValueError: Topic is already assigned

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
from collections import defaultdict, OrderedDict
from types import MappingProxyType
from typing import Any, Optional

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Topic(Publisher, Subscriber):
    def __init__(self):
        Publisher.__init__(self)
        self._subject = None
        self._current_subscriber = None

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)

        if self._subject is not None:
            if len(self._subscriptions) > 1:
                self._subject.unsubscribe(self)
            self._current_subscriber = subscriber
            self._subject.subscribe(self)
            self._current_subscriber = None

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions and self._subject is not None:
            self._subject.unsubscribe(self)

    def emit(self, *args: Any, who: Optional[Publisher]=None) -> None:
        if self._subject is None:
            # method will be replaced by .__call__
            raise TypeError('No subject is assigned to this Topic')

        if self._current_subscriber and who == self._current_subscriber:
            self._current_subscriber.emit(*args, who=self)
        elif who == self._subject:
            self.notify(*args)
        else:
            return self._subject.emit(*args, who=self)

    def __call__(self, *args, **kwargs) -> None:
        raise TypeError('Topic is not callable (for use with | operator).' +
                        ' Use "hub.assign(publisher, topic, [meta])" instead.')

    @property
    def assigned(self):
        return self._subject is not None

    async def wait_for_assignment(self, timeout=None):
        if self.assigned:
            return
        else:
            self._assignment_future = asyncio.get_event_loop().create_future()
            if timeout is None:
                await self._assignment_future
            else:
                await asyncio.wait_for(
                    asyncio.shield(self._assignment_future), timeout)

    @property
    def meta(self) -> dict:
        return getattr(self, '_meta', None)


class Hub:
    def __init__(self, permitted_meta_keys=None):
        self._topics = defaultdict(Topic)
        if permitted_meta_keys is not None:
            self._permitted_meta_keys = set(permitted_meta_keys)
        else:
            self._permitted_meta_keys = None

    def __getitem__(self, topic: str) -> Topic:
        return self._topics[topic]

    def __contains__(self, topic: str) -> bool:
        return topic in self._topics

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
               meta: Optional[dict]=None) -> Topic:

        topic = self[topic_str]

        if topic._subject is not None:
            raise ValueError('Topic is already assigned')
        else:
            topic._subject = publisher

        if topic._subscriptions:
            publisher.subscribe(topic)

        if meta:
            if self._permitted_meta_keys is not None:
                non_keys = set(meta.keys()) - self._permitted_meta_keys
                if non_keys:
                    raise KeyError('Not permitted meta keys: %r' % non_keys)
            setattr(topic, '_meta', meta)  # ._meta is not yet existing

        if hasattr(topic, '_assignment_future'):
            topic._assignment_future.set_result(None)

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
               meta: Optional[dict]=None) -> Topic:

        return self._hub.assign(self._prefix + topic_str, publisher, meta)
