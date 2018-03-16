import collections
import bisect

class AccountDict(collections.MutableMapping):
  def __init__(self):
    self._key_to_index=dict()
    self._revision_list=list()
    self._item_list=list()
    self._actual_revision=0
    
  def __setitem__(self, key, value):
    self._actual_revision+=1
    if key in self._key_to_index:
      self._revision_list.pop(self._key_to_index[key])
      self._item_list.pop(self._key_to_index[key])
    self._key_to_index[key]=len(self._revision_list)
    self._revision_list.append(self._actual_revision)
    self._item_list.append( (key, value) )
    
  def __getitem__(self, key):
    return self._item_list[self._key_to_index[key]][1]
  
  def __delitem__(self, key):
    index=self._key_to_index.pop(key)
    self._revision_list.pop(index)
    self._item_list.pop(index)
  
  def __iter__(self):
    for key in sorted(self._key_to_index, key=self._key_to_index.get):
      yield key

  def __len__(self):
    return len(self._item_list)
  
  def from_revision(self, revision:int=0):
    start_index=bisect.bisect(self._revision_list, revision)
    return dict(self._item_list[start_index:])
  
  def __repr__(self):
    return repr(dict(self))
    
  @property
  def revision(self):
    return self._actual_revision