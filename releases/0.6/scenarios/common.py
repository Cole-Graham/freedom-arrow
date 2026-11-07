"""Shared scenario build: IO, layout overlay, lobby sliders, FA script graft, flavors."""
from pathlib import Path
import copy, hashlib, json, shutil, sys, zipfile
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
    # The lobby compares a hash of the .bascr, so every machine must write the same bytes.
    # Python sets create_system to 0 on Windows and 3 elsewhere; fix it and the file mode.
    with zipfile.ZipFile(target/(name+'.bascr'),'w',zipfile.ZIP_DEFLATED) as w:
        for part,data in [('head.bam',dump(head)),('objects.bam',dump(objects)),('nodes.bam',dump(nodes))]:
            info=zipfile.ZipInfo(part,(2026,11,4,0,0,0));info.create_system=3;info.external_attr=0o600<<16
            w.writestr(info,enc(data),zipfile.ZIP_DEFLATED,compresslevel=6)
    (target/'meta.json').write_bytes(dump(meta))
    print(target)
def read_bascr(folder,name):
    z=zipfile.ZipFile(folder/(name+'.bascr'))
    return load(dec(z.read('head.bam'))),load(dec(z.read('nodes.bam'))),load(dec(z.read('objects.bam'))),load((folder/'meta.json').read_bytes())
# The build reads these native missions from the local game. A different game version would give different maps.
NATIVE_PINS=json.loads((Path(__file__).resolve().parent/'native-pins.json').read_text())
def read_native(game,mission):
    folder=game/'BrokenArrow_Data/StreamingAssets/SharedMissions'/mission
    for f in (folder/(mission+'.bascr'),folder/'meta.json'):
        want=NATIVE_PINS.get(f'{mission}/{f.name}')
        assert want,f'{mission}/{f.name} has no pin in native-pins.json'
        got=hashlib.sha256(f.read_bytes()).hexdigest()
        assert got==want,f'{f} does not match the pinned game version ({got[:16]} != {want[:16]}). Every player must build from the same game version, or install one shared .bamod.'
    return read_bascr(folder,mission)
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
# Editor defaults. Vanilla Central Village_network has only Alpha (0) and Bravo (1).
# 101 is uncaptured/neutral in scoring, not a lobby team. 100 is not the 2.0 Observer waiting-list slot.
EDITOR_SIDES={100,101}
def strip_editor_teams(objects,meta):
    extra={o['_uid'] for o in objects if o.get('_type')==3 and o.get('teamSide') in EDITOR_SIDES}
    drop=extra|{o['_uid'] for o in objects if o.get('_type')==13 and o.get('ownTeam',{}).get('id') in extra}
    objects[:]=[o for o in objects if o['_uid'] not in drop]
    meta['teams']=[t for t in meta.get('teams',[]) if t.get('teamSide') not in EDITOR_SIDES]
    alpha=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']=='Alpha team')
    bravo=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']=='Bravo team')
    for o in objects:
        if o.get('_type')==3 and o['_dname']=='Alpha team':o['teamRelation']={'key':[{'id':bravo,'type':3}],'val':[0]}
        if o.get('_type')==3 and o['_dname']=='Bravo team':o['teamRelation']={'key':[{'id':alpha,'type':3}],'val':[0]}
    assert {o.get('teamSide') for o in objects if o.get('_type')==3}=={0,1}
def vec(p):
    v={k:float(p[k]) for k in 'XYZ'};mag(v);return v
def new_uid(objects):return max(o['_uid'] for o in objects)+1
def add_camera(objects,team,name,pos,look,height=700.0):
    """Start camera for one team. The camera faces its look-at tag (type 6), as on native maps."""
    tid=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']==team)
    one={'X':1.0,'Y':1.0,'Z':1.0,'SqrMagnitude':3.0};still={'X':0.0,'Y':0.0,'Z':0.0,'W':1.0}
    tag=dict(info='',noArrow=False,color=0,pos=vec(look),rotate=dict(still),scale=dict(one),v=1,_uid=new_uid(objects),_type=6,_dname=name+' look at')
    objects.append(tag)
    objects.append(dict(actOnStart=True,aimTag={'id':tag['_uid'],'type':6},aimUnit=None,team={'id':tid,'type':3},player=None,Preview={},
                        pos=vec(pos),height=float(height),rotate=dict(still),scale=dict(one),v=1,_uid=new_uid(objects),_type=18,_dname=name))
def letter_zones(objects,letters,names):
    """letters: authored zone name -> (shown name, value). Renames zones, sets hudText, and keeps only Alpha and Bravo as capturers."""
    zones=[o for o in objects if o.get('_type')==15]
    assert {o['_dname'] for o in zones}==set(letters),sorted(o['_dname'] for o in zones)
    want={str(o['_uid']):letters[o['_dname']][1] for o in zones}
    for name in names:assert want==weights(name),(name,want)
    teams={o['_dname']:o['_uid'] for o in objects if o.get('_type')==3}
    for o in zones:
        o['_dname']=o['hudText']=letters[o['_dname']][0]
        o['capturableBy']=[c for c in o['capturableBy'] if c['id'] in (teams['Alpha team'],teams['Bravo team'])];assert len(o['capturableBy'])==2
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
    if layout is not None:apply_layout(objects,layout);print(f"{flavor['name']} physical layout copied from package {LAYOUT}")
    if flavor['kind']==2:
        start,target=spec['deploy_target'](game) if 'deploy_target' in spec else (163,flavor.get('deploy_target',159))
        add_deployment(nodes,start,target,flavor.get('deploy_pin','in'))
    write_flavor(out,spec,flavor,head,objects,nodes,meta)
def build_template_flavor(game,out,spec,flavor,template):
    head,nodes,objects,meta=copy.deepcopy(template)
    graft_conquest(game,objects,nodes,meta)
    if flavor['kind']==2:add_deployment(nodes,163,flavor['deploy_target'],flavor.get('deploy_pin','in'))
    else:set_bots(objects,meta)
    write_flavor(out,spec,flavor,head,objects,nodes,meta)
# Files beside layout.bascr, such as .png previews, go into every built flavor folder.
SOURCE_ONLY={'__init__.py',LAYOUT+'.bascr','meta.json'}
def copy_assets(out,spec):
    src=Path(sys.modules[spec['prepare'].__module__].__file__).resolve().parent
    for f in sorted(src.iterdir()):
        if f.is_file() and f.name not in SOURCE_ONLY and f.suffix!='.pyc':
            for flavor in spec['flavors']:shutil.copyfile(f,out/flavor['name']/f.name);print(f"{flavor['name']}: copied {f.name}")
def build_pair(game,out,spec):
    layout,template=spec['prepare'](game,spec)
    for flavor in spec['flavors']:
        if flavor.get('host'):build_host_flavor(game,out,spec,flavor,layout)
        else:build_template_flavor(game,out,spec,flavor,template)
    if spec.get('assets',True):copy_assets(out,spec)
# Vanilla maps: the native network and Skirmish missions stay as they are (zones, spawns, cameras, play areas, AI).
# Only the score values, zone visibility, income, money and the online deployment pause change.
def describe(values):
    by={}
    for name,v in values.items():by.setdefault(v,[]).append(name[0])
    parts=[f"{' '.join(sorted(by[v]))} {'is' if len(by[v])==1 else 'are'} worth {v}" for v in sorted(by,reverse=True)]
    return ('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
            'the side with the higher zone value scores the difference. First to 300 wins. '+', '.join(parts)+'. Flat 200 income, no upkeep.')
def drop_zones(objects,nodes,gone):
    """Osama 2026-11-07: the Skirmish map is the master. Remove network-only zones. A size-logic node that shows or hides
    such a zone is spliced out, its flow passed straight on; any other reference stops the build."""
    import json as _j
    for z in gone:
        ref=f"c{z['_uid']}";objects.remove(z)
        assert not [o for o in objects if f'"id": {z["_uid"]},' in _j.dumps(o)],z['_dname']
        for n in [n for n in nodes['b'] if any(p.get('v')==ref for p in n.get('props_v2',[]))]:
            assert n['nnKey']=='objVisible2',(z['_dname'],n['nnKey'])
            ins=[c for c in nodes['c'] if c['a']==n['id']];outs=[c for c in nodes['c'] if c['b']==n['id']]
            assert all(c['c']=='in2' for c in ins) and all(c['d']=='out2' for c in outs),(ins,outs)
            nodes['c']=[c for c in nodes['c'] if n['id'] not in (c['a'],c['b'])]
            nodes['c']+=[dict(a=o['a'],b=i['b'],c=o['c'],d=i['d'],e=i['e']) for i in ins for o in outs]
            nodes['b'].remove(n)
        print(f"zone {z['_dname']} removed: not on the Skirmish map")
def patch_vanilla(head,nodes,objects,meta,flavor,scene,values):
    """values: zone _dname -> value. Sets hudText to the _dname, because some native zones show another zone's name."""
    kind=flavor['kind']
    assert head['GameMode']==kind and head['map']==scene,(head['GameMode'],head['map'])
    drop_zones(objects,nodes,[o for o in objects if o.get('_type')==15 and o['_dname'] not in values])
    zones=[o for o in objects if o.get('_type')==15]
    assert sorted(o['_dname'] for o in zones)==sorted(values),sorted(o['_dname'] for o in zones)
    for o in zones:o['hudText']=o['_dname']
    want={str(o['_uid']):values[o['_dname']] for o in zones}
    assert want==weights(flavor['name']),(flavor['name'],want)
    ids={f"c{o['_uid']}" for o in zones};conquest=shown=caps=0
    for n in nodes['b']:
        props={p['k']:p for p in n.get('props_v2',[])}
        if n.get('nnKey')=='setConquestMode':conquest+=1
        # The native size logic hides outer zones on small lobbies. Every valued zone stays on the map.
        if n.get('nnKey')=='objVisible2' and props['oz2'].get('v') in ids and props['isv']['v']=='False':props['isv']['v']='True';shown+=1
        if n.get('nnKey')=='setIncomeCurveState':props['state']['v']='False'
        if n.get('nnKey')=='setMaxMoney':props['moneyValue']['v']=str(MONEY_CAP);caps+=1
    assert conquest>=1 and caps==(1 if kind==2 else 0),(conquest,caps)
    byid={b['id']:b for b in nodes['b']}
    calcs={c['b'] for c in nodes['c'] if c['d']=='Multiply' and c['c']=='amount' and byid.get(c['a'],{}).get('nnKey')=='setMoney2'}
    assert len(calcs)==(2 if kind==3 else 0),calcs
    for calc in calcs:
        source=[c['b'] for c in nodes['c'] if c['a']==calc and c['c']=='a'];assert len(source)==1
        assert not [c for c in nodes['c'] if c['a']==source[0] and c['c']=='Value'],'money variable has an input'
        nodes['c']=[c for c in nodes['c'] if not (c['a']==calc and c['c']=='B')]
        next(p for p in byid[calc]['props_v2'] if p['k']=='B')['v']='1'
        next(p for p in byid[source[0]]['props_v2'] if p['k']=='Value')['v']=str(START_POINTS)
    slider_defaults(objects,meta,2 if kind==2 else 0)
    print(f"{flavor['name']}: {len(zones)} zones valued, {shown} hidden-zone nodes now show the zone")
def vanilla_spec(scene,network,skirmish,name,guid,values):
    """One vanilla map: network flavor from `network`, Skirmish flavor from `skirmish`. guid gets 'a' (network) and 'b' (Skirmish)."""
    def patch(head,nodes,objects,meta,flavor):patch_vanilla(head,nodes,objects,meta,flavor,scene,values)
    def prepare(game,spec):
        sk=sorted(o['_dname'] for o in read_native(game,skirmish)[2] if o.get('_type')==15)
        assert sk==sorted(values),('values must name exactly the Skirmish zones',sk)
        return None,None
    def deploy_target(game):
        nodes=read_native(game,network)[1];byid={b['id']:b for b in nodes['b']}
        start=[b['id'] for b in nodes['b'] if b.get('nnKey')=='start'];assert len(start)==1,start
        nxt=[c['a'] for c in nodes['c'] if c['b']==start[0] and byid[c['a']]['nnKey']=='testCond2'];assert len(nxt)==1,nxt
        return start[0],nxt[0]
    return dict(author='Freedom Arrow',desc=describe(values),prepare=prepare,assets=False,patch_host=patch,deploy_target=deploy_target,
                flavors=[dict(name=f'[FA] {name} 0.1',guid=guid+'a',kind=2,public=True,host=network),
                         dict(name=f'[FA] {name} Skirmish 0.1',guid=guid+'b',kind=3,public=False,host=skirmish)])
