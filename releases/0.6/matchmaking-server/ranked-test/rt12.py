# Search status for the ranked page (Lateralus 22 Nov: show when the matchmaker widens the rating gap): GetRanked.search.
import sys,os,time,json;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
a=C(B,'7656119966000001','Solo1v1');t=C(B,'7656119966000002','SoloTeam')
print('not searching ->',a.call('GetRanked')['search'])
a.call('FindMatch','r1v1');t.call('FindMatch','rteam');time.sleep(1)
print('1v1 ->',json.dumps(a.call('GetRanked')['search']));print('team ->',json.dumps(t.call('GetRanked')['search']))
time.sleep(30);print('after 31 s, 1v1 ->',json.dumps(a.call('GetRanked')['search']))
