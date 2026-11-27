"""Small deterministic helpers for isolated PLA graph construction."""
import copy,json
from contextlib import contextmanager
from pathlib import Path
BLOCKS=json.loads((Path(__file__).with_name('id-reservations.json')).read_text())['blocks']
def reserved_owner(table,uid):
 """Owner of the reserved block that holds this row ID (mod/id-reservations.json), else None."""
 for b in BLOCKS:
  lo,hi=b['tables'].get(table,b['tables']['*'])
  if lo<=uid<=hi:return b['owner']

class Graph:
 def __init__(self,t,patches,native_ids):
  self.t,self.p,self.native=t,patches,native_ids
  self.next=max(i for rs in t.values() for i in rs)+1
  self.option=max(t['OptionsJson'])+1
  self.owner=None;self.owned=set();self.sealed=False
 @contextmanager
 def scope(self,owner):
  """Rows created inside take IDs from the owner's reserved block. After it, no section may create rows (live sections go above the hook)."""
  assert self.owner is None and any(b['owner']==owner for b in BLOCKS),owner   # ROC branch 27 Nov: one owner block may follow another (plb, then roc); live rows stay sealed
  self.owner=owner
  try:yield
  finally:self.owner=None;self.sealed=True
 def _free(self,table):
  b=next(b for b in BLOCKS if b['owner']==self.owner);lo,hi=b['tables'].get(table,b['tables']['*'])
  uid=next((i for i in range(lo,hi+1) if i not in self.t[table]),None);assert uid,(table,self.owner,'reserved block is full')
  return uid
 def put(self,table,uid,fields):
  if uid not in self.t[table]:
   o=reserved_owner(table,uid)
   assert not (self.sealed and self.owner is None),(table,uid,'new row after the reserved-ID hook: put live sections above roc_hook')
   assert o==self.owner,(table,uid,f'reserved for {o}' if o else f'outside the {self.owner} block','see mod/id-reservations.json')
   if o:self.owned.add((table,uid))
  self.t[table].setdefault(uid,{'Id':uid}).update(copy.deepcopy(fields))
  self.p[table].setdefault(str(uid),{}).update(copy.deepcopy(fields))
  return uid
 def add(self,table,row,fields=None):
  if self.owner:uid=self._free(table)
  else:
   uid=self.option if table=='OptionsJson' else self.next
   if table=='OptionsJson':self.option+=1;assert uid<=32767
   else:self.next+=1
  data=copy.deepcopy(row);data.pop('Id',None);data.update(fields or {})
  return self.put(table,uid,data)
 def rows(self,table,uid):return [r for r in list(self.t[table].values()) if r.get('UnitId')==uid]
 def remove(self,table,uid):
  self.t[table].pop(uid,None)
  if uid in self.native[table]:self.p[table][str(uid)]=None
  else:self.p[table].pop(str(uid),None)
 def clear_unit(self,uid,tables):
  for table in tables:
   for r in self.rows(table,uid):self.remove(table,r['Id'])
 def clear_options(self,uid):
  mids={r['Id'] for r in self.rows('ModificationsJson',uid)}
  for o in list(self.t['OptionsJson'].values()):
   if o['ModificationId'] in mids:self.remove('OptionsJson',o['Id'])
  self.clear_unit(uid,['ModificationsJson'])
