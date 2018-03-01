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
  def __init__(self, collection:'TopicCollection', name:str):
    self._name=name
    self._collection=collection
    self._subscriptions=set()
    self._meta_dict=dict()

  def propose(self, meta_dict: Optional[dict]=None) -> 'Topic':
    if meta_dict:
      self._meta_dict.update(meta_dict)
    if self._subscriptions:
      self._collection.on_subscription(self._name, True)
    return self

  def subscribe(self, callback:Callable[[Any],None]) -> TopicDisposable:
    self._subscriptions.add(callback)
    if len(self._subscriptions)==1:
      self._collection.on_subscription(self._name, True)
    return TopicDisposable(self, callback)

  def unsubscribe(self, callback:Callable[[Any],None]) -> None:
    self._subscriptions.remove(callback)
    if not self._subscriptions:
      self._collection.on_subscription(self._name, False)
  
  def unsubscribe_all(self) -> None:
    if self._subscriptions:
      self._collection.on_subscription(self._name, False)
    self._subscriptions.clear()

  def publish(self, msg_data:Any) -> None:
    for cb in self._subscriptions:
      # TODO: critical place to think about handling exceptions
      cb(msg_data)

class TopicCollection:
  def __init__(self, parent_collection:Optional['TopicCollection']=None, name:str=''):
    self._name=name
    self._parent_collection=parent_collection
    self._topics=dict()
    self._collections=dict()
  
  @property
  def collections(self) -> dict:
    return MappingProxyType(self._collections)
  
  @property
  def topics(self, topic_name) -> dict:
    return MappingProxyType(self._topics)

  def __getitem__(self, topic_name:str) -> Union[Topic, 'TopicCollection']:
    if SEP in topic_name:
      # if SEP is found get the TopicCollection and do __getitem__ there
      collection_name, topic_path=topic_name.split(sep=SEP, maxsplit=1)
      assert collection_name not in self._topics, 'Could not access as TopicCollection as %r is used for a Topic'%collection_name
      if collection_name not in self._collections:
        self._collections[collection_name]=TopicCollection(parent_collection=self, name=collection_name)
      return self._collections[collection_name][topic_path]
    elif topic_name in self._collections: # if it's a topic collection
      return self._collections[topic_name]
    else:
      if topic_name not in self._topics:
        self._topics[topic_name]=Topic(self, topic_name)
      return self._topics[topic_name]

  def unsubscribe_all(self) -> None:
    for topic in self._topics.values():
      topic.unsubscribe_all()
    for collection in self._collections.values():
      collection.unsubscribe_all()
    self._collections.clear()
    self._topics.clear()
  
  def on_subscription(self, topic_name:str, subscribtion:bool):
    pass