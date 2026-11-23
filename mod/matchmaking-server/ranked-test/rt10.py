# Leave cooldowns + end-screen result (Lateralus 22 Nov): leaving a ranked lobby in the deck phase -> 5 min, again -> 1 h;
# a rated 1v1 -> GetRanked.extra.lastResult has every player's before/after/change.
import sys,os,time,json,urllib.request;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from rt_client import C,who
B=os.environ.get('RT_BASE','http://127.0.0.1:8653/hubs/test/hubs')
def lobby(a,b):
    a.call('FindMatch','r1v1');b.call('FindMatch','r1v1');time.sleep(2.5)
    m=a.got('MatchFound')[-1][0];lid=m['lobbyId'];h,o=(a,b) if m['host']==a.steam else (b,a)
    h.call('ReportGameLobby',lid,{'scenario':'[FA] [1v1] '+m['scenario']+' 0.2','invite':{'x':1}});o.call('ConfirmJoined',lid);time.sleep(1.5)
    return m,lid,h,o
# seed (python rt10.py seed DIR): F has 1 expired offence today, H has 2 -> their next leave gives 1 h and 24 h
if len(sys.argv)>2 and sys.argv[1]=='seed':
    import datetime;now=datetime.datetime.now(datetime.timezone.utc);past=(now-datetime.timedelta(hours=1)).isoformat().replace('+00:00','Z')
    epoch=now.replace(hour=0,minute=0,second=0,microsecond=0).isoformat().replace('+00:00','Z')
    json.dump({'epoch':epoch,'players':{'7656119955000006':{'Count':1,'Until':past,'Why':['x']},'7656119955000008':{'Count':2,'Until':past,'Why':['x','y']}}},open(os.path.join(sys.argv[2],'penalties.json'),'w'));sys.exit()
for i,(x,y) in enumerate((('1','2'),('5','6'),('7','8')),1):
    a=C(B,'765611995500000'+x,'P'+x);b=C(B,'765611995500000'+y,'P'+y)
    m,lid,h,o=lobby(a,b)
    if o is a: a,b=b,a;print(f'round {i}: phase',h.call('GetRanked')['match']['phase'])
    o.call('LeaveLobby',lid);time.sleep(1)
    print(f'  {o.name} left -> extra',{k:v for k,v in o.call('GetRanked')['extra'].items() if k!='lastResult'})
    print('  FindMatch again ->',o.call('FindMatch','r1v1'));h.call('CancelFind');time.sleep(0.5)
# rated match with two fresh players
c=C(B,'7656119955000003','C');d=C(B,'7656119955000004','D')
m,lid,h,o=lobby(c,d);h.call('ReportStarted',lid)
mf={x.steam:x.got('MatchFound')[-1][0] for x in (c,d)};side={0:'Alpha',1:'Bravo'};uid={c.steam:1,d.steam:2}
players=[{'uid':uid[x.steam],'team':side[mf[x.steam]['team']],'Deserter':False,'bot':False} for x in (c,d)]
for x in (c,d):
    body={'v':2,'who':who(x.steam),'myUid':uid[x.steam],'scenario':m['scenario'],'matchKey':'k','myTeam':side[mf[x.steam]['team']],'fight':{'WinnerTeam':'Alpha'},'players':players}
    urllib.request.urlopen(urllib.request.Request(B+'/stats/v1/match',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')).read()
time.sleep(1);print('lastResult',json.dumps(c.call('GetRanked')['extra']['lastResult'])[:500])
