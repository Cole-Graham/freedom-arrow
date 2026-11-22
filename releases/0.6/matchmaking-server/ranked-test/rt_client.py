import json,threading,time,urllib.request,websocket,hashlib
RS='\x1e'
class C:
    def __init__(s,base,steam,name,build='b1'):
        s.base=base;s.steam=steam;s.name=name;s.msgs=[];s.res={};s.n=0
        r=json.load(urllib.request.urlopen(urllib.request.Request(base+'/hubs/game/negotiate?negotiateVersion=1',data=b'',method='POST')))
        s.ws=websocket.create_connection(base.replace('http','ws')+'/hubs/game?id='+r['connectionToken'])
        s.ws.send(json.dumps({'protocol':'json','version':1})+RS);s.ws.recv()
        threading.Thread(target=s.loop,daemon=True).start()
        s.call('HelloKeyed',steam,name,build,'0.10.31','FA 0.9.5','k')
    def loop(s):
        buf=''
        while True:
            try:buf+=s.ws.recv()
            except Exception:return
            while RS in buf:
                m,buf=buf.split(RS,1);d=json.loads(m)
                if d.get('type')==1:s.msgs.append((d['target'],d['arguments']))
                elif d.get('type')==3:s.res[d['invocationId']]=d
    def call(s,t,*a):
        s.n+=1;i=str(s.n);s.ws.send(json.dumps({'type':1,'invocationId':i,'target':t,'arguments':list(a)})+RS)
        for _ in range(100):
            if i in s.res:
                d=s.res.pop(i)
                if d.get('error'):return {'error':d['error']}
                return d.get('result')
            time.sleep(0.05)
        return {'error':'timeout'}
    def got(s,t):return [a for (x,a) in s.msgs if x==t]
def who(steam):return hashlib.sha256(('arrow-stats|'+steam).encode()).hexdigest()[:16]
def stats(base,steam,myteam,winner,players=None,key='L1_100_Alpha'):
    body={'v':2,'who':who(steam),'scenario':'[FA] [1v1] Kadaga 0.1','matchKey':key,'myTeam':myteam,'fight':{'WinnerTeam':winner},'players':players or []}
    return json.load(urllib.request.urlopen(urllib.request.Request(base+'/hubs/stats/v1/match',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')))
