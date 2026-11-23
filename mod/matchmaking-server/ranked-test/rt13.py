# Map size tag (Lateralus 22 Nov 20:1x): a ranked 1v1 whose lobby runs the [2v2] map of the same name is unrated; the [1v1] map stays rated.
import sys,os,time,json,glob;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs');DIR=os.environ['RT_DIR']
def run(tag,n):
    P=[C(B,f'7656119923{n}{i:05d}',f'{tag}{i}') for i in range(2)]
    for p in P:p.call('FindMatch','r1v1');time.sleep(0.05)
    time.sleep(3)
    m=P[0].got('MatchFound')[-1][0];host=next(p for p in P if p.steam==m['host'])
    host.call('ReportGameLobby',m['lobbyId'],{'scenario':f'[FA] [{tag}] '+m['scenario']+' 0.2','invite':{'x':1}});host.call('ReportStarted',m['lobbyId'])
    time.sleep(1.5);return m['lobbyId'],m['scenario']
ok=True
for tag,n,want in (('2v2',1,True),('1v1',2,False)):
    lid,scen=run(tag,n)
    ev=[json.loads(l) for f in glob.glob(os.path.join(DIR,'**','*.jsonl'),recursive=True) for l in open(f) if lid in l]
    un=[e for e in ev if 'unrated' in json.dumps(e)]
    got=bool(un and 'map_wrong_size' in json.dumps(un))
    print(f'[{tag}] {scen}: unrated(map_wrong_size)={got} expected {want}');ok&=got==want
print('PASS' if ok else 'FAIL')
