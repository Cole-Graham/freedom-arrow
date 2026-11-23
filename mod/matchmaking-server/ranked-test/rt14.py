# 0.9.6 team queue (Lateralus 23 Nov 2026): one team queue makes 2v2, 3v3 or 4v4, largest first; 2v2/3v3 only after a 20 s gather;
# parties of up to 4 (4 = 4v4 only); maps.json gives the exact map (scenarioName) and the size check.
import sys,os,time,json,glob;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs');DIR=os.environ['RT_DIR']
ok=True
def check(c,msg):
    global ok;ok&=bool(c);print(('PASS ' if c else 'FAIL ')+msg)
def party(leader,members):
    for m in members:
        leader.call('PartyAction','invite',m.steam,None);time.sleep(0.2)
        pid=m.call('PartyAction','state',None,None)['incoming'][0]['partyId'];m.call('PartyAction','accept',None,pid)
def found(ps):return [p.got('MatchFound')[-1][0] if p.got('MatchFound') else None for p in ps]
def unrated(lid):return [json.loads(l) for f in glob.glob(os.path.join(DIR,'**','*.jsonl'),recursive=True) for l in open(f) if lid in l and '"unrated"' in l]
# 1. 8 solos -> one 4v4 at once
P=[C(B,f'76561199240{i:05d}',f'Big{i}') for i in range(8)]
for p in P:p.call('FindMatch','rteam')
time.sleep(3);f=found(P)
check(all(x and x['format']=='4v4' for x in f),f"8 solos -> 4v4 within 3 s: {[x and x['format'] for x in f]}")
check(all(x and (x.get('scenarioName') or '').startswith('[FA] [4v4] ') for x in f),f"scenarioName {f[0] and f[0].get('scenarioName')}")
# 2. 4 solos -> nothing at 5 s, a 2v2 after the 20 s gather
Q=[C(B,f'76561199241{i:05d}',f'Duo{i}') for i in range(4)]
for p in Q:p.call('FindMatch','rteam')
time.sleep(5);check(not any(found(Q)),'4 solos: no match before 20 s')
time.sleep(18);f=found(Q)
check(all(x and x['format']=='2v2' for x in f),f"4 solos -> 2v2 after the gather: {[x and x['format'] for x in f]}")
check(f[0] and (f[0].get('scenarioName') or '').startswith('[FA] [2v2] '),f"scenarioName {f[0] and f[0].get('scenarioName')}")
# 3. wrong-size map in that 2v2 -> unrated map_wrong_size; 4. right map -> rated (no unrated line)
m=f[0];h=next(p for p in Q if p.steam==m['host'])
h.call('ReportGameLobby',m['lobbyId'],{'scenario':'[FA] [4v4] Airport 0.2','invite':{'x':1}});h.call('ReportStarted',m['lobbyId']);time.sleep(1.5)
check(any('map_wrong_size' in json.dumps(u) for u in unrated(m['lobbyId'])),'2v2 match on the [4v4] Airport map -> unrated (map_wrong_size)')
# 5. 6 solos -> a 3v3 after the gather (not 2v2 + 2 waiting)
S=[C(B,f'76561199242{i:05d}',f'Tri{i}') for i in range(6)]
for p in S:p.call('FindMatch','rteam')
time.sleep(23);f=found(S)
check(all(x and x['format']=='3v3' for x in f),f"6 solos -> 3v3: {[x and x['format'] for x in f]}")
m=f[0];h=next(p for p in S if p.steam==m['host'])
h.call('ReportGameLobby',m['lobbyId'],{'scenario':m['scenarioName'],'invite':{'x':1}});h.call('ReportStarted',m['lobbyId']);time.sleep(1.5)
check(not unrated(m['lobbyId']),f"3v3 on its own map {m['scenarioName']} -> stays rated")
# 6. party of 5 refused; party of 4 + 4 solos -> 4v4 at once
F=[C(B,f'76561199243{i:05d}',f'Five{i}') for i in range(5)];party(F[0],F[1:])
r=F[0].call('FindMatch','rteam');check('party_too_big' in json.dumps(r),f'party of 5 -> {r}')
G=[C(B,f'76561199244{i:05d}',f'Four{i}') for i in range(4)];party(G[0],G[1:])
H=[C(B,f'76561199245{i:05d}',f'Solo{i}') for i in range(4)]
print(' party of 4 ->',G[0].call('FindMatch','rteam'))
for p in H:p.call('FindMatch','rteam')
time.sleep(3);f=found(G+H)
check(all(x and x['format']=='4v4' for x in f),f"party of 4 + 4 solos -> 4v4: {[x and x['format'] for x in f]}")
print('PASS' if ok else 'FAIL')
