"""Small deterministic helpers for isolated PLA graph construction."""
import copy

class Graph:
 def __init__(self,t,patches,native_ids):
  self.t,self.p,self.native=t,patches,native_ids
  self.next=max(i for rs in t.values() for i in rs)+1
  self.option=max(t['OptionsJson'])+1
 def put(self,table,uid,fields):
  self.t[table].setdefault(uid,{'Id':uid}).update(copy.deepcopy(fields))
  self.p[table].setdefault(str(uid),{}).update(copy.deepcopy(fields))
  return uid
 def add(self,table,row,fields=None):
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
