"""
Use an iterable and emit each value

Usage:

>>> from broqer import op
>>> l = [1, 2, 3]
>>> s = op.FromIterable(l)

>>> _disposable = s | op.sink(print)
1
2
3

>>> l.append(4)
>>> _disposable2 = s | op.sink(print, 'Second sink:')
Second sink: 1
Second sink: 2
Second sink: 3
Second sink: 4
"""
from broqer import Publisher, Subscriber, SubscriptionDisposable


class FromIterable(Publisher):
    def __init__(self, iterable) -> None:
        Publisher.__init__(self)
        self._iterable = iterable

    def subscribe(self, subscriber: Subscriber,
                  prepend: bool=False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)
        for value in self._iterable:
            subscriber.emit(value, who=self)
        return disposable

    def get(self):
        return next(self._iterable)
