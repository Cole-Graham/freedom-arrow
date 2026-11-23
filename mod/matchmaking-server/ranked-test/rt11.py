# Draw rule (Lateralus 22 Nov 'use your draw proposal'): 3v3 draw with seeded ratings; every change must match the formula here.
# Seed: RT_SEED_DIR gets season-1-team.json before the hub starts (see rt8 seed below), RT_FILL = filler rating (0 = none).
import sys,os,time,json,math,urllib.request;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C,who
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
R={f'7656119922000{i:04d}':v for i,v in enumerate((1500,1600,1550,1460,1420,1400))}
if len(sys.argv)>1 and sys.argv[1]=='seed':
    fill=float(sys.argv[3]);rows=[{'SteamId':k,'Name':'C'+k[-1],'Rating':v,'Wins':3,'Losses':3,'Best':v} for k,v in R.items()]
    rows+=[{'SteamId':f'f{i}','Name':f'F{i}','Rating':fill,'Wins':3,'Losses':3,'Best':fill} for i in range(30)] if fill>0 else []
    json.dump(rows,open(os.path.join(sys.argv[2],'season-1-team.json'),'w'));sys.exit()
K=40;E=lambda a,b:1/(1+10**((b-a)/400))
P=[C(B,k,'C'+k[-1]) for k in R]
for p in P:p.call('FindMatch','rteam');time.sleep(0.05)
time.sleep(3)
mf={p.steam:p.got('MatchFound')[-1][0] for p in P}
m=next(iter(mf.values()));lid=m['lobbyId'];host=next(p for p in P if p.steam==m['host'])
host.call('ReportGameLobby',lid,{'scenario':'[FA] [3v3] '+m['scenario']+' 0.2','invite':{'x':1}});host.call('ReportStarted',lid)
side={0:'Alpha',1:'Bravo'};uid={p.steam:i+1 for i,p in enumerate(P)}
players=[{'uid':uid[p.steam],'team':side[mf[p.steam]['team']],'Deserter':False,'bot':False} for p in P]
for p in P:
    body={'v':2,'who':who(p.steam),'myUid':uid[p.steam],'scenario':m['scenario'],'matchKey':'k','myTeam':side[mf[p.steam]['team']],'fight':{'WinnerTeam':'Neutral'},'players':players}
    urllib.request.urlopen(urllib.request.Request(B+'/stats/v1/match',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
time.sleep(1.5)
W=[p.steam for p in P if mf[p.steam]['team']==0];L=[p.steam for p in P if mf[p.steam]['team']==1]
rw=sum(R[x] for x in W)/3;rl=sum(R[x] for x in L)/3;base=K*(1-E(rw,rl))
fill=float(os.environ.get('RT_FILL','0'));allr=list(R.values())+([fill]*30 if fill>0 else []);mean=sum(allr)/len(allr);gate=min(1,max(0,(1500-mean)/100))
def bonus(r):d=1700-r;return 0 if d<=200 else (1-math.exp(-d/100))*gate
exp={}
for S,O in ((W,L),(L,W)):
    os_=sum(R[x] for x in S)/3;oe=sum(R[x] for x in O)/3;pot=3*K*(0.5-E(os_,oe));raw=[K*(0.5-E(R[x],oe)) for x in S];sh=(sum(raw)-pot)/3
    for x,v in zip(S,raw):exp[x]=v-sh
ok=True
print(f'winners avg {rw:.1f} vs losers avg {rl:.1f}; same-for-all base {base:.2f}; ladder mean {mean:.0f} gate {gate:.2f}')
for p in P:
    r=p.got('RankedResult');got=r[-1][0]['change'] if r else None;e=round(exp[p.steam],2)
    ok&=got is not None and abs(got-e)<0.02
    print(f"  {R[p.steam]:.0f} {'A' if p.steam in W else 'B'} hub {got:+.2f} formula {e:+.2f}")
print('sums: A',round(sum(exp[x] for x in W),2),'B',round(sum(exp[x] for x in L),2),'match',round(sum(exp.values()),4));print('PASS' if ok else 'FAIL')
