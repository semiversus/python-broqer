"""
RevisionDict works like an ordinary dictionary with additional revision
keeping of changes. Basically the following attribute and two methods are
important:

* .revision - returning the actual revision as integer (starting with 0)
* .key_to_revision(key) - return the revision when the given key was changed
* .checkout(start=0) - return a dict with changes older than `start`

>>> d=RevisionDict()
>>> d.revision                    # get revision (is 0 at init)
0

Adding new items:
>>> d['a']=0; d['b']=1; d['c']=2  # make three updates
>>> d.revision                    # showing 3 changes
3

Inspecting content of RevisionDict:
>>> d.checkout()=={'a': 0, 'b': 1, 'c': 2} # get a dictionary with all changes
True
>>> d.checkout(2)                 # get all changes starting with rev. 2
{'c': 2}
>>> d.checkout(3)                 # all changes starting with actual revision
{}
>>> d.key_to_revision('b')        # revision where 'b' was changed last time
2
>>> d
RevisionDict([_Item(key='a', value=0, revision=1), \
_Item(key='b', value=1, revision=2), \
_Item(key='c', value=2, revision=3)])

Update items:
>>> d['b']=3                      # update value of 'b' (was 2 before)
>>> d.revision
4
>>> d.key_to_revision('b')
4
>>> d.checkout(3)                 # get all changes starting with rev. 3
{'b': 3}
>>> tuple(d.keys())               # iterate over keys (they are sorted by rev.)
('a', 'c', 'b')
"""

__author__="Günther Jena"

import collections
import bisect


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
    self._actual_revision=0 # number of actual revision
    
  def __setitem__(self, key, value):
    """ set value for given key and update the actual revision """
    self._actual_revision+=1
    if key in self._key_to_index:
      # if this key already available remove entry from self._items
      del self[key]
    self._key_to_index[key]=len(self._items) # indexing the end of self._items
    self._items.append(_Item(key, value, self._actual_revision))
    
  def __getitem__(self, key):
    """ return value to the given key """
    return self._items[self._key_to_index[key]].value
  
  def __delitem__(self, key):
    """ remove key from this collection """
    index=self._key_to_index.pop(key) # get (and remove) index for this key
    self._items.pop(index) # remove that item entry
    self._key_to_index.update( # update indicies for keys
      ((k,i-1) for (k,i) in self._key_to_index.items() if i>index) )
  
  def __iter__(self):
    """ returns a iterator over the keys sorted by revision """
    return iter( sorted(self._key_to_index, key=self._key_to_index.get) )

  def __len__(self):
    """ return number of items """
    return len(self._items)
  
  def key_to_revision(self, key):
    """ get revision when this key was updated last time """
    return self._items[self._key_to_index[key]].revision
    
  def checkout(self, start=None):
    """ get a dict() with all changes from revision `start` on """
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

if __name__=='__main__':
  import doctest
  doctest.testmod()