from collections import defaultdict
from typing import Any, Optional, Callable

from broqer import Publisher, Subscriber, SubscriptionDisposable


class ProxySubject(Publisher, Subscriber):
    def __init__(self):
        super().__init__()
        self._subject = None

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if len(self._subscriptions) == 1 and self._subject is not None:
            # if this was the first subscription
            self._subject.subscribe(self)
        return disposable

    def unsubscribe(self, subscriber: 'Subscriber') -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions and self._subject is not None:
            self._subject.unsubscribe(self)

    def emit(self, *args: Any, who: Optional[Publisher]=None) -> None:
        if self._subject is None:
            # method will be replaced by .__call__
            raise TypeError('No subject is assigned to this ProxySubject')
        elif who == self._subject:
            self._emit(*args)
        elif who != self._subject:
            self._subject.emit(*args)

    def __call__(self, *args, **kwargs) -> None:
        raise TypeError('ProxySubject is not callable (for use as operator).' +
                        'Use |hub.publish(path, meta) instead.')

    @property
    def assigned(self):
        return self._subject is not None

    @property
    def meta(self):
        return getattr(self, '_meta', None)

    @meta.setter
    def meta(self, meta_dict):
        if hasattr(self, '_meta'):
            raise ValueError('ProxySubject already has a meta dict')
        self._meta = meta_dict


class Hub:
    def __init__(self):
        self._proxies = defaultdict(ProxySubject)

    def __getitem__(self, path: str) -> ProxySubject:
        return self._proxies[path]

    def publish(self, path: str, meta: Optional[dict]=None) \
            -> Callable[[Publisher], Publisher]:
        proxy = self[path]
        if meta:
            proxy.meta = meta

        def _build(publisher):
            # used for pipeline style assignment
            if proxy._subject is not None:
                raise ValueError('ProxySubject is already assigned')
            else:
                proxy._subject = publisher

            if len(proxy._subscriptions):
                proxy._subject.subscribe(proxy)

            return proxy
        return _build


class SubordinateHub:
    def __init__(self, hub, prefix):
        self._hub = hub
        self._prefix = prefix

    def __getitem__(self, path: str) -> ProxySubject:
        return self._hub._proxies[self._prefix + path]

    def publish(self, path: str, meta: dict) -> ProxySubject:
        return self._hub.publish(self._prefix + path, meta)

    def resolve(self, path: str) -> str:
        return self._prefix + path
