from broqer.disposable import Disposable
from collections import defaultdict
from typing import Callable, Any, Optional, Union
from types import MappingProxyType
from functools import partial

SEP='.' # separator used for hierarchy

class TopicDisposable(Disposable):
  def __init__(self, topic: 'Topic', callback: Callable[[Any], None]) -> None:
    self._topic=topic
    self._callback=callback

  def dispose(self) -> None:
    self._topic.unsubscribe(self._callback)

class Topic:
  def __init__(self, hub:'Hub', name:str):
    self._hub=hub
    self._name=name

    self._subscriptions=set()
    self._meta_dict=dict()
    self._subscription_callback=None

  def propose(self, meta_dict: Optional[dict]=None, subscription_callback:Optional[Callable[['Topic', bool],None]]=None) -> 'Topic':
    if meta_dict:
      self._meta_dict.update(meta_dict)
    self._subscription_callback=subscription_callback
    if self._subscription_callback and self._subscriptions:
      self._subscription_callback(self, True)
    return self

  def subscribe(self, callback:Callable[[Any],None]) -> TopicDisposable:
    self._subscriptions.add(callback)
    if self._subscription_callback and len(self._subscriptions)==1:
      self._subscription_callback(self, True)
    return TopicDisposable(self, callback)

  def unsubscribe(self, callback:Callable[[Any],None]) -> None:
    self._subscriptions.remove(callback)
    if self._subscription_callback and not self._subscriptions:
      self._subscription_callback(self, False)
  
  def unsubscribe_all(self) -> None:
    if self._subscription_callback and self._subscriptions:
      self._subscription_callback(self, False)
    self._subscriptions.clear()

  def publish(self, msg_data:Any) -> None:
    for cb in self._subscriptions:
      # TODO: critical place to think about handling exceptions
      cb(msg_data)
  
  @property
  def hub(self):
    return self._hub
  
  @property
  def name(self):
    return self._name

  @property
  def path(self):
    return self._hub._prefix()+self._name
  
  @property
  def meta(self):
    return MappingProxyType(self._meta_dict)

class Hub:
  def __init__(self, parent_hub:Optional['Hub']=None, name:str=''):
    self._name=name
    self._parent_hub=parent_hub
    self._topics=dict()
    self._hubs=dict()
  
  @property
  def hubs(self) -> dict:
    return MappingProxyType(self._hubs)
  
  @property
  def topics(self, topic_name) -> dict:
    return MappingProxyType(self._topics)

  @property
  def parent_hub(self):
    return self._parent_hub
  
  @property
  def name(self):
    return self._name
  
  @property
  def path(self):
    if self._parent_hub:
      return self.parent_hub._prefix() + self._name
    elif self._name:
      return self._name
    else:
      return ''
  
  def _prefix(self):
    if self._parent_hub:
      return self._parent_hub._prefix()+self._name+SEP
    elif self._name:
      return self._name+SEP
    else:
      return ''
  
  def __iter__(self):
    for topic in self._topics.values():
      yield topic.path
    for hub in self._hubs.values():
      yield from iter(hub)

  def __getitem__(self, topic_name:str) -> Union[Topic, 'Hub']:
    if SEP in topic_name:
      # if SEP is found get the Hub and do __getitem__ there
      hub_name, topic_path=topic_name.split(sep=SEP, maxsplit=1)
      assert hub_name not in self._topics, 'Could not access as Hub as %r is used for a Topic'%hub_name
      if hub_name not in self._hubs:
        self._hubs[hub_name]=Hub(parent_hub=self, name=hub_name)
      return self._hubs[hub_name][topic_path]
    elif topic_name in self._hubs: # if it's a topic hub
      return self._hubs[topic_name]
    else:
      if topic_name not in self._topics:
        self._topics[topic_name]=Topic(self, topic_name)
      return self._topics[topic_name]

  def unsubscribe_all(self) -> None:
    for topic in self._topics.values():
      topic.unsubscribe_all()
    for hub in self._hubs.values():
      hub.unsubscribe_all()
    self._hubs.clear()
    self._topics.clear()