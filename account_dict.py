import collections
import bisect
import itertools

class _Item():
  """_Item representing a key:value pair with information about the revision number this update was done."""

  __slots__= 'key', 'value', 'revision'

  def __init__(self, key, value, revision):
    self.key=key
    self.value=value
    self.revision=revision

  def __lt__(self, other):
    """__lt__ method is used for bisect"""
    return self.revision<other.revision
  
  def __repr__(self):
    return '(key=%r, value=%r, revision=%r)'%(self.key, self.value, self.revision)

class AccountDict(collections.MutableMapping):
  def __init__(self):
    self._key_to_index=dict()
    self._items=list()
    self._actual_revision=0
    
  def __setitem__(self, key, value):
    self._actual_revision+=1
    if key in self._key_to_index:
      self._items.pop(self._key_to_index[key])
    self._key_to_index[key]=len(self._items)
    self._items.append(_Item(key, value, self._actual_revision))
    
  def __getitem__(self, key):
    return self._items[self._key_to_index[key]].value
  
  def __delitem__(self, key):
    index=self._key_to_index.pop(key)
    self._items.pop(index)
    self._key_to_index.update(((key,_index-1) for (key,_index) in self._key_to_index.items() if _index>index))
  
  def __iter__(self):
    return iter(sorted(self._key_to_index, key=self._key_to_index.get))

  def __len__(self):
    return len(self._items)
  
  def key_to_revision(self, key):
    return self._items[self._key_to_index[key]].revision
    
  def copy(self, start=None, end=None):
    start_index=0
    end_index=len(self._items)-1

    if start is not None:
      start_index=bisect.bisect(self._items, _Item(None, None, start))

    if end is not None:
      end_index=bisect.bisect(self._items, _Item(None, None, end))

    d=AccountDict()
    d._items=self._items[start_index:end_index]
    d._key_to_index=dict( ((k,v) for (k,v) in self._key_to_index.items() if start_index<=v<=end_index) )
    d._actual_revision=self._actual_revision
    return d
  
  def __repr__(self):
    return '%s(%r)'%(self.__class__.__name__, self._items)

  @property
  def revision(self):
    return self._actual_revision