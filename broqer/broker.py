from broqer.persistance import InMemPersistanceMgr
from broqer.disposable import Disposable
from collections import defaultdict
from functools import partial

class TopicDisposable(Disposable):
  def __init__(self, topic, callback):
    self._topic=topic
    self._callback=callback

  def dispose(self):
    self._topic.unsubscribe(self._callback)

class Topic:
  def __init__(self, broker):
    self._broker=broker
    self._subscriptions=set()
    self._meta_dict=dict()
    self._on_subscription_callback=None

  def propose(self, meta_dict=None, persistent=False, on_subscription_callback=None):
    if meta_dict:
      self._meta_dict.update(meta_dict)
    if persistent:
      self._broker._persistance_mgr.add_topic(self)
    self._on_subscription_callback=on_subscription_callback
    if self._on_subscription_callback and self._subscriptions:
      self._on_subscription_callback(True)

  def subscribe(self, callback):
    self._subscriptions.add(callback)
    if self._on_subscription_callback and len(self._subscriptions)==1:
      self._on_subscription_callback(True)
    return TopicDisposable(self, callback)

  def unsubscribe(self, callback):
    self._subscriptions.remove(callback)
    if self._on_subscription_callback and not self._subscriptions:
      self._on_subscription_callback(False)
  
  def unsubscribe_all(self):
    if self._on_subscription_callback and self._subscriptions:
      self._on_subscription_callback(False)
    self._subscriptions.clear()

  def publish(self, msg_data):
    for cb in self._subscriptions:
      cb(msg_data)

class Broker:
  def __init__(self, persistance_mgr=None):
    if persistance_mgr is None:
      self._persistance_mgr=InMemPersistanceMgr()
    else:
      self._persistance_mgr=persistance_mgr
    self._topics=defaultdict(partial(Topic, self))

  def __getitem__(self, topic_name):
    return self._topics[topic_name]

  def purge(self):
    for topic in self._topics.values():
      topic.unsubscribe_all()
    self._persistance_mgr.purge()
