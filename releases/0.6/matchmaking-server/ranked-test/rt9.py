# Reconnect keeps the ranked deck (Lateralus 22 Nov: ArrowQueue's reconnect made the next FindMatch 'deck_invalid').
import sys,os,time;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
a=C(B,'76561199440000001','Recon',deck=True);time.sleep(0.3);a.ws.close();time.sleep(0.5)
b=C(B,'76561199440000001','Recon',deck=False)   # new session, no SetRankedDeck
print('after reconnect, FindMatch r1v1 ->',b.call('FindMatch','r1v1'))
n=C(B,'76561199440000002','Never',deck=False)
print('never reported, FindMatch r1v1 ->',n.call('FindMatch','r1v1'))
