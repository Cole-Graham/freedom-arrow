# Deserter rule: a player the game flags Deserter never gains, even when his team wins (3v3, one winner leaves).
import sys,os,time,json,urllib.request;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C,who
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
P=[C(B,f'7656119900000{i:04d}',f'P{i}') for i in range(6)]
for p in P:p.call('FindMatch','rteam')
time.sleep(2.5)
mf={p.steam:p.got('MatchFound')[-1][0] for p in P}
m=next(iter(mf.values()));lid=m['lobbyId'];host=next(p for p in P if p.steam==m['host'])
host.call('ReportGameLobby',lid,{'scenario':'[FA] [3v3] '+m['scenario']+' 0.2','invite':{'x':1}});host.call('ReportStarted',lid)
side={0:'Alpha',1:'Bravo'};uid={p.steam:i+1 for i,p in enumerate(P)}
A=[p for p in P if mf[p.steam]['team']==0];Bt=[p for p in P if mf[p.steam]['team']==1]
deserter=A[0]
players=[{'uid':uid[p.steam],'team':side[mf[p.steam]['team']],'Deserter':p is deserter,'bot':False} for p in P]
for p in P:
    if p is deserter:continue
    body={'v':2,'who':who(p.steam),'myUid':uid[p.steam],'scenario':m['scenario'],'matchKey':'k','myTeam':side[mf[p.steam]['team']],'fight':{'WinnerTeam':'Alpha'},'players':players}
    urllib.request.urlopen(urllib.request.Request(B+'/stats/v1/match',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
time.sleep(1)
for p in P:
    r=p.got('RankedResult');print(p.name,'team',mf[p.steam]['team'],'deserter' if p is deserter else '','->',r[-1][0] if r else None)
