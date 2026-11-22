import sys,time;sys.path.insert(0,'/tmp/heli3')
from rt_client import C
B='http://127.0.0.1:8652'
h=C(B,'p1','High');l=C(B,'p2','Low')
h.call('PartyAction','invite','p2',None);time.sleep(0.2);pid=l.call('PartyAction','state',None,None)['incoming'][0]['partyId'];l.call('PartyAction','accept',None,pid)
print('spread 600 ->',h.call('FindMatch','r3v3'))
print('member tries ->',l.call('FindMatch','r3v3'))
