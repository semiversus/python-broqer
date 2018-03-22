"""Provides a way to get dictionary changes since a given revision."""

__author__="Günther Jena"

import collections
import bisect
import itertools

class _Item(collections.namedtuple('_Item', 'key value revision')):
  """ _Item representing a key:value pair with information about the revision
  this update was done.
  """

  def __lt__(self, other):
    """__lt__ method is used for bisect"""
    return self.revision<other.revision

class RevisionDict(collections.MutableMapping):
  def __init__(self):
    self._items=list() # keeping _Item objects, guaranteed sorted by revision
    self._key_to_index=dict() # dict indexing position of key in self._items
    self._actual_revision=1
    
  def __setitem__(self, key, value):
    if key in self._key_to_index:
      # if this key already available remove entry from self._items
      del self[key]
    self._key_to_index[key]=len(self._items) # indexing the end of self._items
    self._items.append(_Item(key, value, self._actual_revision))
    self._actual_revision+=1
    
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
  
  def key_to_revision(self, key):
    """ get revision when this key was updated last time """
    return self._items[self._key_to_index[key]].revision
    
  def checkout(self, start=None):
    """ Get a dict() with all changes from revision `start` on """
    if start is not None:
      start_index=bisect.bisect(self._items, _Item(None, None, start))
    else:
      start_index=None
    return dict(((i.key, i.value) for i in self._items[start_index:]))
  
  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__, self._items)

  @property
  def revision(self):
    """ get latest revision """
    return self._actual_revision