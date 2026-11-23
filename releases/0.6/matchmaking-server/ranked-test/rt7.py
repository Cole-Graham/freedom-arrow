# Ladder-average bonus gate (Lateralus 22 Nov): two new 1000 players, 1v1, Alpha wins. Seed the ladder before the hub starts (RT_SEED mean).
import sys,os,time,json,urllib.request;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C,who
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
P=[C(B,f'7656119911000{i:04d}',f'G{i}') for i in range(2)]
for p in P:p.call('FindMatch','r1v1')
time.sleep(2.5)
mf={p.steam:p.got('MatchFound')[-1][0] for p in P}
m=next(iter(mf.values()));lid=m['lobbyId'];host=next(p for p in P if p.steam==m['host'])
host.call('ReportGameLobby',lid,{'scenario':'[FA] [1v1] '+m['scenario']+' 0.2','invite':{'x':1}});host.call('ReportStarted',lid)
side={0:'Alpha',1:'Bravo'};uid={p.steam:i+1 for i,p in enumerate(P)}
players=[{'uid':uid[p.steam],'team':side[mf[p.steam]['team']],'Deserter':False,'bot':False} for p in P]
for p in P:
    body={'v':2,'who':who(p.steam),'myUid':uid[p.steam],'scenario':m['scenario'],'matchKey':'k','myTeam':side[mf[p.steam]['team']],'fight':{'WinnerTeam':'Alpha'},'players':players}
    urllib.request.urlopen(urllib.request.Request(B+'/stats/v1/match',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
time.sleep(1)
for p in P:
    r=p.got('RankedResult');print(p.name,side[mf[p.steam]['team']],'->',{k:r[-1][0][k] for k in ('change','rating','win')} if r else None)
