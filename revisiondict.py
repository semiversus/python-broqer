"""Provides a way to get dictionary changes since a given timestamp."""

__author__="Günther Jena"

import collections
import bisect
import itertools

class _Item(collections.namedtuple('_Item', 'key value timestamp')):
  """ _Item representing a key:value pair with information about the timestamp
  this update was done.
  """

  def __lt__(self, other):
    """__lt__ method is used for bisect"""
    return self.timestamp<other.timestamp

class RevisionDict(collections.MutableMapping):
  def __init__(self, timestamp_cb=None):
    self._items=list() # keeping _Item objects, guaranteed sorted by timestamp
    self._key_to_index=dict() # dict indexing position of key in self._items
    if timestamp_cb is None:
      # if no timestamp_cb is given use a count generator starting at 1
      self._timestamp_cb=itertools.count(start=1).__next__
    else:
      self._timestamp_cb=timestamp_cb
    
  def __setitem__(self, key, value):
    if key in self._key_to_index:
      # if this key already available remove entry from self._items
      del self[key]
    self._key_to_index[key]=len(self._items) # indexing the end of self._items
    self._items.append(_Item(key, value, self._timestamp_cb()))
    
  def __getitem__(self, key):
    return self._items[self._key_to_index[key]].value
  
  def __delitem__(self, key):
    index=self._key_to_index.pop(key) # get (and remove) index for this key
    self._items.pop(index) # remove that item entry
    self._key_to_index.update( # update indicies for keys
      ((k,i-1) for (k,i) in self._key_to_index.items() if i>index) )
  
  def __iter__(self):
    return iter( sorted(self._key_to_index, key=self._key_to_index.get) )

  def __len__(self):
    return len(self._items)
  
  def key_to_timestamp(self, key):
    return self._items[self._key_to_index[key]].timestamp
    
  def checkout(self, start=None):
    if start is not None:
      start_index=bisect.bisect(self._items, _Item(None, None, start))
    else:
      start_index=None
    return dict(((i.key, i.value) for i in self._items[start_index:]))
  
  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__, self._items)

  @property
  def timestamp(self):
    return self._items[-1].timestamp