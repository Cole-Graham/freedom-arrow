"""Shared scenario build: IO, layout overlay, lobby sliders, FA script graft, flavors."""
from pathlib import Path
import copy, hashlib, json, sys, zipfile
from Crypto.Cipher import AES
ROOT=Path(__file__).resolve().parent.parent;REPO=ROOT.parent.parent
sys.path.insert(0,str(REPO))
from pipeline.crypto import AES_KEY
MARKER=b'fhk3s0g3'
GAME_VERSION='1.2.2'
START_POINTS=1500
MATCH_MINUTES=45
MONEY_CAP=100000
NETWORK_HOST='Central Village_network'
SKIRMISH_HOST='Central_Village_Skirmish'
KEEP={'_uid','_dname','_type'};PLAYER_KEEP=KEEP|{'isBot'};LAYOUT_TYPES={3,7,10,13,15,18}
LAYOUT='layout'
def dec(raw):
    assert raw[:8]==MARKER
    p=AES.new(AES_KEY,AES.MODE_CBC,raw[8:24]).decrypt(raw[24:]);return p[:-p[-1]]
def enc(p):
    iv=hashlib.sha256(p).digest()[:16];n=16-len(p)%16
    return MARKER+iv+AES.new(AES_KEY,AES.MODE_CBC,iv).encrypt(p+bytes([n])*n)
def load(b):return json.loads(b.decode('utf-8-sig'))
def dump(o):return json.dumps(o,indent=2,ensure_ascii=False).encode('utf-8')
def settings():return json.loads((ROOT/'source/UserData/FAConquestPrototype/settings.json').read_text())
def weights(name):return settings()['MapZoneWeights'][name]
def deploy_seconds():return settings()['OnlineDeploySeconds']
def slider_defaults(objects,meta,want_money):
    money=[o for o in objects if o.get('desc')=='ui_lobby_StartMoney_desc']+[o for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_StartMoney_desc']
    assert len(money)==want_money
    for o in money:
        o['defV']=START_POINTS
        if 'tstV' in o:o['tstV']=START_POINTS
    timers=[o for o in objects if o.get('desc')=='ui_lobby_Timer_desc']+[o for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_Timer_desc']
    assert len(timers)==2
    for o in timers:
        o['defV']=MATCH_MINUTES
        if 'tstV' in o:o['tstV']=MATCH_MINUTES
def add_deployment(nodes,start,target,pin='in'):
    wire={'a':target,'b':start,'c':pin,'d':'flow','e':start}
    assert wire in nodes['c'],wire
    nodes['c'].remove(wire)
    assert not {n['nnKey'] for n in nodes['b']}&{'pauseGame'}
    first=max(n['id'] for n in nodes['b'])+1
    on,wait,off=first,first+1,first+2
    def node(i,key,props,x):return dict(v=0,nnKey=key,px=x,py=-900.0,id=i,rtpt=True,props_v2=[dict(k=k,v=v,t=1) for k,v in props])
    nodes['b']+=[node(on,'pauseGame',[('val','True')],-800.0),node(wait,'delay',[('Time',str(deploy_seconds())),('igGmSp','True')],-500.0),node(off,'pauseGame',[('val','False')],-200.0)]
    nodes['c']+=[dict(a=on,b=start,c='in',d='flow',e=start),dict(a=wait,b=start,c='in2',d='flow',e=start),dict(a=off,b=wait,c='in',d='out2',e=wait),dict(a=target,b=off,c=pin,d='out',e=off)]
def mag(v):v['SqrMagnitude']=v['X']*v['X']+v['Y']*v['Y']+v['Z']*v['Z']
def identity(q):return q['X']==0 and q['Y']==0 and q['Z']==0 and q['W']==1
def world_x_half(o):
    q=o['rotate'];rx=o['scale']['X']/2;rz=o['scale']['Z']/2;y,w=q['Y'],q['W']
    a=1-2*y*y;b=2*w*y
    return (a*a*rx*rx+b*b*rz*rz)**0.5
def spawn_index(spawns,o):
    peers=[x for x in spawns if x['team']['id']==o['team']['id'] and x['spawnType2']==o['spawnType2']]
    peers=sorted(peers,key=lambda x:(x['pos']['Z'],x['pos']['X'],x['_uid']))
    return peers.index(o)
def role(o,spawns):
    t=o['_type']
    if t==15:return ('zone',o.get('hudText') or o['_dname'])
    if t==10:return ('spawn',o['team']['id'],tuple(o['spawnType2']),spawn_index(spawns,o))
    if t==7:return ('playable',)
    if t==18:return ('camera',o['team']['id'])
    if t==3:return ('team',o['_dname'])
    if t==13:return ('player',o['_dname'])
def overlay(dst,src,skip):
    for k,v in src.items():
        if k not in skip:dst[k]=copy.deepcopy(v)
def extract_layout(objects):
    spawns=[o for o in objects if o.get('_type')==10];layout={};play=None
    for o in objects:
        t=o.get('_type')
        if t==7:play=o;continue
        if t in LAYOUT_TYPES:
            r=role(o,spawns);assert r not in layout,r;layout[r]=o
    assert play is not None;layout[('playable',)]=play;return layout
def apply_layout(objects,layout):
    spawns=[o for o in objects if o.get('_type')==10];dest={}
    for o in objects:
        t=o.get('_type')
        if t==7:dest.setdefault(('playable',),[]).append(o);continue
        if t in LAYOUT_TYPES:
            r=role(o,spawns);assert r not in dest,r;dest[r]=o
    for r,src in layout.items():
        if r==('playable',):
            assert dest.get(r)
            for o in dest[r]:overlay(o,src,KEEP)
            continue
        assert r in dest,r
        overlay(dest[r],src,PLAYER_KEEP if r[0]=='player' else KEEP)
def write(out,name,head,objects,nodes,meta):
    target=out/name;target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target/(name+'.bascr'),'w',zipfile.ZIP_DEFLATED) as w:
        for part,data in [('head.bam',dump(head)),('objects.bam',dump(objects)),('nodes.bam',dump(nodes))]:
            w.writestr(zipfile.ZipInfo(part,(2026,11,4,0,0,0)),enc(data),zipfile.ZIP_DEFLATED)
    (target/'meta.json').write_bytes(dump(meta))
    print(target)
def read_bascr(folder,name):
    z=zipfile.ZipFile(folder/(name+'.bascr'))
    return load(dec(z.read('head.bam'))),load(dec(z.read('nodes.bam'))),load(dec(z.read('objects.bam'))),load((folder/'meta.json').read_bytes())
def read_native(game,mission):
    return read_bascr(game/'BrokenArrow_Data/StreamingAssets/SharedMissions'/mission,mission)
def read_layout(mod_file):
    return read_bascr(Path(mod_file).resolve().parent,LAYOUT)
def stamp(head,meta,name,guid,desc,author,kind,public):
    head.update(guid=guid,name=name,author=author,desc=desc,IsDevVersion=False,devId=0,public=public,GameMode=kind)
    meta.pop('devid',None)
    meta.update(guid=guid,scenario=name,author=author,desc=desc,public=public,type=kind,gameVersion=GAME_VERSION)
def set_bots(objects,meta):
    fight={o['_uid'] for o in objects if o.get('_type')==3 and o['_dname'] in ('Alpha team','Bravo team')}
    n=0
    for o in objects:
        if o.get('_type')==13 and o.get('ownTeam',{}).get('id') in fight:
            o['isBot']=True;n+=1
    assert n>=2,n
    for t in meta.get('teams',[]):
        if t.get('teamName') in ('Alpha team','Bravo team'):
            for s in t.get('slots',[]):s['bot']=True
def graft_conquest(game,objects,nodes,meta):
    nn,no,nm=read_native(game,NETWORK_HOST)[1:]
    want={69:'ui_lobby_StartMoney_desc',70:'ui_lobby_Income_desc',72:'ui_lobby_Timer_desc'}
    assert not want.keys()&{o['_uid'] for o in objects}
    added=[copy.deepcopy(o) for o in no if o['_uid'] in want];assert {o['_uid']:o['desc'] for o in added}==want
    objects+=added
    meta['pblOpt']=[copy.deepcopy(o) for o in nm['pblOpt'] if o['id'] in want];assert {o['id']:o['desc'] for o in meta['pblOpt']}==want
    slider_defaults(objects,meta,2)
    keys={22:'getPblInt',136:'setConquestMode',161:'setMaxMoney',162:'setIncomeCurveState',163:'start'}
    script=[copy.deepcopy(b) for b in nn['b'] if b['id'] in keys];assert {b['id']:b['nnKey'] for b in script}==keys
    for b in script:
        if b['id']==162:next(p for p in b['props_v2'] if p['k']=='state')['v']='False'
        if b['id']==161:next(p for p in b['props_v2'] if p['k']=='moneyValue')['v']=str(MONEY_CAP)
    wires=[c for c in nn['c'] if (c['a'],c['b']) in {(136,22),(161,163),(162,163)}];assert len(wires)==3
    wires.append(dict(a=136,b=163,c='in2',d='flow',e=163))
    nodes.update(b=script,c=wires)
def write_flavor(out,spec,flavor,head,objects,nodes,meta):
    stamp(head,meta,flavor['name'],flavor['guid'],spec['desc'],spec['author'],flavor['kind'],flavor['public'])
    write(out,flavor['name'],head,objects,nodes,meta)
def build_host_flavor(game,out,spec,flavor,layout):
    head,nodes,objects,meta=read_native(game,flavor['host'])
    spec['patch_host'](head,nodes,objects,meta,flavor)
    apply_layout(objects,layout);print(f"{flavor['name']} physical layout copied from package {LAYOUT}")
    if flavor['kind']==2:add_deployment(nodes,163,flavor.get('deploy_target',159),flavor.get('deploy_pin','in'))
    write_flavor(out,spec,flavor,head,objects,nodes,meta)
def build_template_flavor(game,out,spec,flavor,template):
    head,nodes,objects,meta=copy.deepcopy(template)
    graft_conquest(game,objects,nodes,meta)
    if flavor['kind']==2:add_deployment(nodes,163,flavor['deploy_target'],flavor.get('deploy_pin','in'))
    else:set_bots(objects,meta)
    write_flavor(out,spec,flavor,head,objects,nodes,meta)
def build_pair(game,out,spec):
    layout,template=spec['prepare'](game,spec)
    for flavor in spec['flavors']:
        if flavor.get('host'):build_host_flavor(game,out,spec,flavor,layout)
        else:build_template_flavor(game,out,spec,flavor,template)
