"""Shared scenario build: IO, layout overlay, lobby sliders, FA script graft, flavors."""
from pathlib import Path
import copy, hashlib, json, shutil, sys, uuid, zipfile
from Crypto.Cipher import AES
ROOT=Path(__file__).resolve().parent.parent;REPO=ROOT.parent
sys.path.insert(0,str(REPO))
from pipeline.crypto import AES_KEY
MARKER=b'fhk3s0g3'
# The game version written into every built map (meta.json gameVersion). It is the game the package runs on: 1.2.2.1 since the
# 0.9.0-dev.20 port (Lateralus 16 Nov 2026: "Why would the build change the editor version stamp?" -- it was left at 1.2.2).
GAME_VERSION='1.2.2.1'
# Editor versions accepted in a source layout. A layout from any other version stops the build for a check.
SOURCE_VERSIONS=('1.2.2','1.2.2.1')
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
    # Osama 18 Nov 2026 15:1x (thread 1571014792016171120): "make sure on all maps, if someone contests a point, it neutralizes it". A zone's
    # forceNeutral flag does that; dev.43 had it off on all 12 Dam zones (Dam, Dam Skirmish, PvE Dam), on everywhere else (Lateralus 21:51 UTC:
    # "Dam zones don't neutralize with multiple players in them"). Set here so every map, PvE included, gets it.
    for o in objects:
        if o.get('_type')==15:o['forceNeutral']=True
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
# graft_conquest adds lobby objects with these fixed UIDs (from the native network host).
GRAFT_UIDS={69,70,72}
def free_uids(objects,nodes,uids=GRAFT_UIDS):
    """Move objects that use a reserved UID to new UIDs and update every {'id','type'} link to them."""
    moved={}
    for o in objects:
        if o['_uid'] in uids:new=new_uid(objects);moved[(o['_uid'],o['_type'])]=new;o['_uid']=new
    assert not [n for n in nodes['b'] if any(p.get('v') in {f'c{u}' for u,_ in moved} for p in n.get('props_v2',[]))],'script links to a moved object'
    def walk(v):
        if isinstance(v,dict):
            if set(v)=={'id','type'} and (v['id'],v['type']) in moved:v['id']=moved[(v['id'],v['type'])]
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(objects)
    return moved
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
# Zone capture time of the vanilla maps. Lateralus 2026-11-12: every FA map uses it unless we design otherwise.
CAPTURE_SECONDS=15.0
# Lateralus 14 Nov 2026: "all maps should allow all 5 slots on each team". Every flavor must have 5 players and 5 lobby
# slots on Alpha and on Bravo, whatever the map's size tag.
SLOTS_PER_TEAM=5
def check_slots(name,objects,meta):
    fight={o['_uid']:o['_dname'] for o in objects if o.get('_type')==3 and o['_dname'] in ('Alpha team','Bravo team')}
    players={t:sum(1 for o in objects if o.get('_type')==13 and o.get('ownTeam',{}).get('id')==u) for u,t in fight.items()}
    slots={t.get('teamName'):len(t.get('slots',[])) for t in meta.get('teams',[]) if t.get('teamName') in fight.values()}
    assert len(fight)==2 and set(players.values())=={SLOTS_PER_TEAM} and set(slots.values())=={SLOTS_PER_TEAM},(name,players,slots)
    # Lateralus 16 Nov 2026: "Klaipeda 1v1 and some other 1v1 maps only have 2 available slots, none of our maps should have unavailable
    # slots". A slot's "lock" in the map file makes it unavailable in the lobby (End's maps locked slots 2-5). How many are open by default
    # is the runtime's job (LobbySlotDefaults.cs), not the map's.
    locked=[(t.get('teamName'),i) for t in meta.get('teams',[]) if t.get('teamName') in fight.values() for i,x in enumerate(t.get('slots',[])) if x.get('lock')]
    assert not locked,(name,'locked lobby slots',locked)
# Every FA map ends at the global ScoreLimit (300). Lateralus 16 Nov 2026: "Honestly just make it 300 for all maps" (the 1v1 limit of
# 100, Osama 6 and 15 Nov, is removed; MapScoreLimits stays empty). The description must say the same limit.
def check_limit(name,desc):
    limit=settings()['ScoreLimit']
    assert name not in settings().get('MapScoreLimits',{}) and f'First to {limit} wins' in desc,(name,f'every FA map ends at {limit}: no MapScoreLimits entry, and the description says so')
# Lateralus 16 Nov 2026: "during the deployment time you can't see the zone values, nor can you see the players and objective details at
# the top of the screen". The online script was start -> pause -> wait -> unpause -> setConquestMode (and the rest), so the conquest mode,
# its top bar and our zone values only appeared after deployment. The rest of the script now starts with the pause, as on F8 Skirmish
# (where the runtime pauses after the mode exists); the pause, wait and unpause stay as they are.
def conquest_during_deployment(nodes):
    start,on,wait,off,after=deployment(nodes)
    nodes['c'].remove(after)
    nodes['c'].append(dict(a=after['a'],b=start,c=after['c'],d='flow',e=start))
    assert not [c for c in nodes['c'] if c['b']==off],'unpause must lead nowhere now'
    deployment_in_time_limit(nodes)
# Lateralus 16 Nov 2026: "the match-clock DOES run during deployment". Online, the room server's match clock runs from the moment
# conquest starts, which is now the start of the deployment pause. Each setConquestMode gets the deployment minutes added to its time
# limit (lobby Timer + 3 with the game's calc3 node, as in the native network missions), so 45:00 is left when deployment ends. The
# runtime (conquest/Mod.cs) holds the shown clock and the FA ledger at 0 elapsed for the deployment.
def deployment_in_time_limit(nodes):
    assert deploy_seconds()%60==0,'OnlineDeploySeconds must be whole minutes'
    extra=deploy_seconds()//60
    for sc in [b for b in nodes['b'] if b['nnKey']=='setConquestMode']:
        limit=[c for c in nodes['c'] if c['a']==sc['id'] and c['c']=='TimeLimitMin']
        if not limit:
            p=next(p for p in sc['props_v2'] if p['k']=='TimeLimitMin');p['v']=str(int(p['v'])+extra);continue
        assert len(limit)==1,limit
        flows=[c for c in nodes['c'] if c['a']==sc['id'] and c['c'].startswith('in')];assert flows,'setConquestMode has no flow input'
        calc=max(b['id'] for b in nodes['b'])+1
        nodes['b'].append(dict(v=0,nnKey='calc3',px=sc['px']-300.0,py=sc['py']-250.0,id=calc,rtpt=True,
            props_v2=[dict(k='B',v=str(extra),t=1),dict(k='Round',v='True',t=3)]))
        src=limit[0]
        nodes['c'].remove(src)
        nodes['c'].append(dict(a=calc,b=src['b'],c='a',d=src['d'],e=src['e']))
        nodes['c'].append(dict(a=sc['id'],b=calc,c='TimeLimitMin',d='Plus',e=calc))
        pins={c['c'] for c in flows};assert len(pins)==1,pins
        for c in flows:c['a']=calc;c['c']='in2'
        nodes['c'].append(dict(a=sc['id'],b=calc,c=pins.pop(),d='out2',e=calc))
# Every ground spawn (not the air spawns, spawnType2 5, which sit off the map) must be inside the active playable zone
# (Lateralus 16 Nov 2026: a Dead Center 2v2 ground spawn was outside it).
def check_spawns(name,head,objects):
    import math
    pz=[o for o in objects if o.get('_type')==7 and o['_uid']==head['spz']];assert len(pz)==1,(name,'active playable zone')
    pz=pz[0];q=pz.get('rotate',{'Y':0.0,'W':1.0});ang=2*math.atan2(q['Y'],q['W'])
    out=[]
    for s in objects:
        if s.get('_type')!=10 or 5 in s.get('spawnType2',[]):continue
        dx=s['pos']['X']-pz['pos']['X'];dz=s['pos']['Z']-pz['pos']['Z']
        lx=dx*math.cos(ang)-dz*math.sin(ang);lz=dx*math.sin(ang)+dz*math.cos(ang)
        if abs(lx)>pz['scale']['X']/2 or abs(lz)>pz['scale']['Z']/2:out.append((s['_uid'],s['spawnType2'],round(s['pos']['X']),round(s['pos']['Z'])))
    assert not out,(name,'ground spawns outside the playable zone',out)
# Lateralus 21 Nov 2026 ("queue both"): online the unmodded server decides a 45:00 time-out by the map's native War Goals victory points
# (a phase point per capture goal 200/400/600 and per destruction goal 100/200/300, all zones equal), not by the FA score (Highway 20 Nov:
# FA 277-154 Bravo, server 9-4 Alpha). The FA host now sends its winner 5 s before time up (conquest ModeControls). With the goals out of
# reach and destruction off neither team earns a victory point, so when FA scores a draw and sends nothing the server's tie rule
# (ConquestMode.GetWinner: equal victory points) gives a draw instead of a winner. Offline the FA ledger already decides (Mod.cs Winner).
NATIVE_GOAL=1000000
def native_goals_out_of_reach(name,nodes):
    modes=[b for b in nodes['b'] if b['nnKey']=='setConquestMode'];assert modes,(name,'no setConquestMode')
    for sc in modes:
        wired={c['c'] for c in nodes['c'] if c['a']==sc['id']}
        props={p['k']:p for p in sc['props_v2']}
        for k,v in (('goal1',NATIVE_GOAL),('goal2',NATIVE_GOAL),('goal3',NATIVE_GOAL),('isDestructionEnabled','False'),('deathByScore','False')):
            assert k in props and k not in wired,(name,k,'missing or wired')
            props[k]['v']=str(v)
# Lateralus 23 Nov 2026 (Coal Mountain): "Make sure all the zones can neutralize, have the right capture times, spawns are facing the right
# way, there are spawn cameras, spawns on each side of the map belong to the right teams, zone icons match ... Is it possible to
# automatically make sure all maps I ask you to add, always check all these things". Every online and Skirmish flavor of every PvP map
# goes through check_layout on every build; a new map that breaks a rule stops the build. Neutralize (forceNeutral) and capture time
# (CAPTURE_SECONDS) are set on every zone in write and write_flavor; slots, play area, native goals and the score limit have their own
# checks. The exceptions below are maps that shipped before these checks; each is kept as authored until it is changed on purpose.
SPAWN_FACING_LIMIT=45   # degrees between a spawn's facing and the direction to the centre of the zones
SPAWN_FACING_KEPT={'[FA] [2v2] Highway of Death','[FA] [2v2] Chkalovsk Airbase','[FA] [4v4] Airport','[FA] [4v4] Cold Harbor'}   # Lateralus's facings, 47-79 degrees
ZONE_ICON_KEPT=set()   # Chkalovsk Foxtrot showed icon 8 (H) until 0.9.6 (fixed in chkalovsk_2v2, Lateralus 23 Nov 2026)
WAYPOINTS_KEPT={'[FA] [2v2] Chkalovsk Airbase'}   # three native waypoints, no unit uses them
def base_name(name):return name.rsplit(' ',1)[0].replace(' Skirmish','')
def letter_icon(zone):return ord((zone.get('hudText') or zone['_dname'])[0])-ord('A')+1
def spawn_offset(spawn,centre):
    import math
    yaw=math.degrees(2*math.atan2(spawn['rotate']['Y'],spawn['rotate']['W']))
    want=math.degrees(math.atan2(centre[0]-spawn['pos']['X'],centre[1]-spawn['pos']['Z']))
    return (yaw-want+180)%360-180
def zone_centre(objects):
    zones=[o['pos'] for o in objects if o.get('_type')==15]
    return sum(p['X'] for p in zones)/len(zones),sum(p['Z'] for p in zones)/len(zones)
def face_spawn_outliers(objects,limit=SPAWN_FACING_LIMIT):
    """Turn only the spawns that face more than limit degrees away from the centre of the zones; keep the author's other facings."""
    import math
    cx,cz=zone_centre(objects);turned={}
    for o in objects:
        if o.get('_type')==10 and abs(spawn_offset(o,(cx,cz)))>limit:
            before=round(spawn_offset(o,(cx,cz)))
            half=math.atan2(cx-o['pos']['X'],cz-o['pos']['Z'])/2
            o['rotate']=dict(X=0.0,Y=math.sin(half),Z=0.0,W=math.cos(half));turned[o['_dname']]=before
    return turned
def remove_units_and_waypoints(objects,units,waypoints):
    """Editor test units (type 1) and waypoints (type 19) out of the map. The counts guard against a changed upload."""
    gone={(o['_uid'],o['_type']) for o in objects if o.get('_type') in (1,19)}
    got=(sum(1 for u,t in gone if t==1),sum(1 for u,t in gone if t==19));assert got==(units,waypoints),('units, waypoints',got)
    objects[:]=[o for o in objects if (o['_uid'],o.get('_type')) not in gone]
    def walk(v):
        if isinstance(v,dict):
            assert not (set(v)=={'id','type'} and (v['id'],v['type']) in gone),('still linked to a removed object',v)
            for x in v.values():walk(x)
        elif isinstance(v,list):
            for x in v:walk(x)
    walk(objects)
def check_layout(name,head,objects):
    base=base_name(name)
    teams={o['_uid']:o['_dname'] for o in objects if o.get('_type')==3}
    zones=[o for o in objects if o.get('_type')==15]
    # zone values: one value for every zone, no value for a zone that is not there
    assert sorted(str(o['_uid']) for o in zones)==sorted(weights(name)),(name,'zones and MapZoneWeights differ')
    # zone icons: Alpha shows A (1), Bravo B (2) ...
    if base not in ZONE_ICON_KEPT:
        bad=[(o.get('hudText'),o.get('ZoneIcon')) for o in zones if o.get('ZoneIcon')!=letter_icon(o)];assert not bad,(name,'zone icon does not match its letter',bad)
    # zones capturable by Alpha and Bravo only, inside the active play area
    for o in zones:assert sorted(teams[c['id']] for c in o['capturableBy'])==['Alpha team','Bravo team'],(name,o.get('hudText'),'capturable by')
    import math
    pz=next(o for o in objects if o.get('_type')==7 and o['_uid']==head['spz']);q=pz.get('rotate',{'Y':0.0,'W':1.0});ang=2*math.atan2(q['Y'],q['W'])
    def inside(p):
        dx=p['X']-pz['pos']['X'];dz=p['Z']-pz['pos']['Z']
        return abs(dx*math.cos(ang)-dz*math.sin(ang))<=pz['scale']['X']/2 and abs(dx*math.sin(ang)+dz*math.cos(ang))<=pz['scale']['Z']/2
    assert all(inside(o['pos']) for o in zones),(name,'zone outside the play area')
    # no editor test units; no waypoints
    assert not [o for o in objects if o.get('_type')==1],(name,'units on the map')
    if base not in WAYPOINTS_KEPT:assert not [o for o in objects if o.get('_type')==19],(name,'waypoints on the map')
    # one start camera per team, starting on its own
    cams=sorted(teams[o['team']['id']] for o in objects if o.get('_type')==18 and o.get('actOnStart'))
    assert cams==['Alpha team','Bravo team'],(name,'one start camera per team',cams)
    # spawns: each team's spawns on its own side of the line halfway between the two teams' spawns
    sp=[o for o in objects if o.get('_type')==10];cen={}
    for t in ('Alpha team','Bravo team'):
        ps=[o['pos'] for o in sp if teams[o['team']['id']]==t];assert ps,(name,t,'no spawns')
        cen[t]=(sum(p['X'] for p in ps)/len(ps),sum(p['Z'] for p in ps)/len(ps))
    (ax,az),(bx,bz)=cen['Alpha team'],cen['Bravo team'];mx,mz=(ax+bx)/2,(az+bz)/2
    wrong=[(o['_dname'],teams[o['team']['id']]) for o in sp if (((o['pos']['X']-mx)*(ax-mx)+(o['pos']['Z']-mz)*(az-mz))>0)!=(teams[o['team']['id']]=='Alpha team')]
    assert not wrong,(name,'spawns on the other team\'s side',wrong)
    # spawns face the zones
    if base not in SPAWN_FACING_KEPT:
        c=zone_centre(objects);off=[(o['_dname'],round(spawn_offset(o,c))) for o in sp if abs(spawn_offset(o,c))>SPAWN_FACING_LIMIT]
        assert not off,(name,f'spawns facing more than {SPAWN_FACING_LIMIT} degrees away from the zones (C.face_spawn_outliers turns them)',off)
def write_flavor(out,spec,flavor,head,objects,nodes,meta):
    check_slots(flavor['name'],objects,meta)
    check_layout(flavor['name'],head,objects)
    native_goals_out_of_reach(flavor['name'],nodes)
    check_spawns(flavor['name'],head,objects)
    if flavor['kind']==2:conquest_during_deployment(nodes)
    check_limit(flavor['name'],spec['desc'])
    for o in objects:
        if o.get('_type')==15:o['capTime']=CAPTURE_SECONDS
    stamp(head,meta,flavor['name'],flavor['guid'],spec['desc'],spec['author'],flavor['kind'],flavor['public'])
    write(out,flavor['name'],head,objects,nodes,meta)
def build_host_flavor(game,out,spec,flavor,layout):
    head,nodes,objects,meta=read_native(game,flavor['host'])
    spec['patch_host'](head,nodes,objects,meta,flavor)
    if layout is not None:apply_layout(objects,layout);print(f"{flavor['name']} physical layout copied from package {LAYOUT}")
    if flavor['kind']==2:
        add_deployment(nodes,163,flavor.get('deploy_target',159),flavor.get('deploy_pin','in'))
    write_flavor(out,spec,flavor,head,objects,nodes,meta)
def build_template_flavor(game,out,spec,flavor,template):
    head,nodes,objects,meta=copy.deepcopy(template)
    graft_conquest(game,objects,nodes,meta)
    if flavor['kind']==2:add_deployment(nodes,163,flavor['deploy_target'],flavor.get('deploy_pin','in'))
    else:set_bots(objects,meta)
    write_flavor(out,spec,flavor,head,objects,nodes,meta)

# End's 1v1 maps (Steam Workshop, 1-3 Nov 2026; Osama 15 Nov 2026 00:54 PST: "End said we can use his maps here and implement them
# into our mod"; 01:01 "these are 1v1"). All five share one shape: stock conquest script (start, delay, two pauses,
# setConquestMode 300 points / 45 min), zones Alpha-Echo with no values, 5 slots per team, no units or cameras. The FA conquest
# graft replaces the script. Bravo is the centre zone on all five (nearest the midpoint of the two teams' spawns).
# Lateralus 16 Nov 2026: "Klaipeda / Kadaga / Jelgava 1v1: A B C - 2 points, D E - 4 points"; Central Village removed ("not suitable
# designs"; Runtime.cs RetiredScenarios deletes the installed copies by GUID). Chernyakhovsky is now Lateralus's own design (chernyakhovsky_1v1).
END_SCRIPT=sorted(['start','delay','pauseGame','pauseGame','setConquestMode'])
END_VALUES=dict(Alpha=2,Bravo=2,Charlie=2,Delta=4,Echo=4)
def prepare_end(mod_file,scene,spec,facing=None):
    """facing: team name -> compass yaw in degrees (0 north, 90 east) for all that team's spawns; End left every spawn at 0."""
    head,nodes,objects,meta=read_layout(mod_file)
    assert head['map']==scene and head['author']=='End' and meta['gameVersion'] in SOURCE_VERSIONS,(head['map'],head['author'])
    assert not [o for o in objects if o.get('_type') in (1,18)],'authored map has units or cameras now. Check this merge.'
    assert sorted(b['nnKey'] for b in nodes['b'])==END_SCRIPT,'End changed his script. Check this merge.'
    nodes.update(b=[],c=[])   # the FA conquest graft supplies the script
    strip_editor_teams(objects,meta)
    for t in meta['teams']:
        for x in t['slots']:x['lock']=False   # End locked slots 2-5 (Lateralus 16 Nov 2026: every slot available)
    assert free_uids(objects,nodes)=={}
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    letter_zones(objects,{n:(n,v) for n,v in END_VALUES.items()},[f['name'] for f in spec['flavors']])
    import math
    teams={o['_uid']:o['_dname'] for o in objects if o.get('_type')==3}
    for team,deg in (facing or {}).items():
        sp=[o for o in objects if o.get('_type')==10 and teams[o['team']['id']]==team];assert sp,(scene,team)
        for o in sp:
            assert identity(o['rotate']),(scene,o['_dname'],'End changed this facing. Check this merge.')
            o['rotate']=dict(X=0.0,Y=math.sin(math.radians(deg)/2),Z=0.0,W=math.cos(math.radians(deg)/2))
    pz=[o['_uid'] for o in objects if o.get('_type')==7];assert len(pz)==1 and head['spz'] in (0,pz[0])
    head['spz']=pz[0]   # some of End's files leave the active play area unset; the other FA maps name their one play area
    add_team_cameras(objects)
    return extract_layout(objects),(head,nodes,objects,meta)
def end_spec(mod_file,title,scene,steam_id,facing=None):
    import uuid
    name=f'[FA] [1v1] {title} 0.1';skirmish=f'[FA] [1v1] {title} Skirmish 0.1'
    spec=dict(author='End',desc=describe(END_VALUES)+f' Map by End (Steam Workshop {steam_id}).',flavors=[
        dict(name=name,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,name)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
        dict(name=skirmish,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,skirmish)),kind=3,public=False)])
    spec['prepare']=lambda game,sp:prepare_end(mod_file,scene,sp,facing)
    spec['asset_dir']=Path(mod_file).resolve().parent
    return spec
# End's 1v1 maps for the new occupation scoring (27 Nov 2026, #ai-ops: "The zones should all be +1 zones for the new occ, add the proper
# occupation game mod like in other maps, and add for both sides the starting camera location between their two respective ground spawns").
# These files have no script, zones with icon 0 and no active play area, so prepare_end does not take them.
# Lateralus 27 Nov 2026 set the zone values per map (Mountain all 2; Below the Mountain A C E 2, B D 4), so each map passes its own.
def prepare_end_occ(mod_file,scene,spec,zones,values,turned,edit=None):
    """zones: End's zone names in letter order (Alpha first); values: letter name -> zone value, Alpha first. turned: UIDs of the spawns more than 45 degrees off, which get turned
    (End names spawns alike, so they are compared by UID). edit(objects) runs before the spawns are turned, for map-specific fixes."""
    head,nodes,objects,meta=read_layout(mod_file)
    assert head['map']==scene and head['author']=='End' and meta['gameVersion'] in SOURCE_VERSIONS and head['dlc']==meta['dlc']==[3]
    assert not nodes['b'] and not nodes['c'] and not [o for o in objects if o.get('_type') in (1,18,19)],'End added a script, units or cameras. Check this merge.'
    strip_editor_teams(objects,meta)
    assert not [x for t in meta['teams'] for x in t['slots'] if x['lock']]
    letters={z:v for z,v in zip(zones,values.items())};assert len(letters)==len(zones)==len(values)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==0,o['_dname'];o['ZoneIcon']=list(letters).index(o['_dname'])+1
    letter_zones(objects,letters,[f['name'] for f in spec['flavors']])
    pz=[o['_uid'] for o in objects if o.get('_type')==7];assert len(pz)==1 and head['spz']==0
    head['spz']=pz[0]   # End left the active play area unset; the other FA maps name their one play area
    if edit:edit(objects)
    before={o['_uid']:dict(o['rotate']) for o in objects if o.get('_type')==10}
    face_spawn_outliers(objects)
    assert {o['_uid'] for o in objects if o.get('_type')==10 and o['rotate']!=before[o['_uid']]}==set(turned)
    add_team_cameras(objects,ground=True)
    return extract_layout(objects),(head,nodes,objects,meta)
def end_occ_spec(mod_file,title,scene,steam_id,zones,values,turned,edit=None):
    import uuid
    name=f'[FA] [1v1] {title} 0.1';skirmish=f'[FA] [1v1] {title} Skirmish 0.1'
    spec=dict(author='End',desc=describe(values)+f' Map by End (Steam Workshop {steam_id}).',flavors=[
        dict(name=name,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,name)),kind=2,public=True,deploy_target=136,deploy_pin='in2'),
        dict(name=skirmish,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,skirmish)),kind=3,public=False)])
    spec['prepare']=lambda game,sp:prepare_end_occ(mod_file,scene,sp,zones,values,turned,edit)
    spec['asset_dir']=Path(mod_file).resolve().parent
    return spec
# Files beside layout.bascr, such as .png previews, go into every built flavor folder.
SOURCE_ONLY={'__init__.py',LAYOUT+'.bascr','meta.json'}
def copy_assets(out,spec):
    src=Path(spec['asset_dir']) if 'asset_dir' in spec else Path(sys.modules[spec['prepare'].__module__].__file__).resolve().parent
    for f in sorted(src.iterdir()):
        if f.is_file() and f.name not in SOURCE_ONLY and f.suffix!='.pyc':
            for flavor in spec['flavors']:shutil.copyfile(f,out/flavor['name']/f.name);print(f"{flavor['name']}: copied {f.name}")
def build_pair(game,out,spec):
    layout,template=spec['prepare'](game,spec)
    for flavor in spec['flavors']:
        if flavor.get('host'):build_host_flavor(game,out,spec,flavor,layout)
        else:build_template_flavor(game,out,spec,flavor,template)
    if spec.get('assets',True):copy_assets(out,spec)
def describe(values,limit=300):
    by={}
    for name,v in values.items():by.setdefault(v,[]).append(name[0])
    parts=[f"{' '.join(sorted(by[v]))} {'is' if len(by[v])==1 else 'are'} worth {v}" for v in sorted(by,reverse=True)]
    return ('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
            f'the side with the higher zone value scores the difference. First to {limit} wins. '+', '.join(parts)+'. Flat 200 income, no upkeep.')
# Lateralus's authored maps (12 November 2026 onward) keep their own script, cameras and play area. The online flavor is
# his file; the Skirmish flavor drops the deployment pause, as the other FA Skirmish flavors do, and fills every slot with bots.
def prepare_authored(mod_file,scene,letters,names,edit=None):
    """edit(head,nodes,objects,meta) runs first, for map-specific script changes."""
    head,nodes,objects,meta=read_layout(mod_file)
    assert head['map']==scene and head['GameMode']==2 and meta['gameVersion'] in SOURCE_VERSIONS,(head['map'],head['GameMode'])
    if edit:edit(head,nodes,objects,meta)
    strip_editor_teams(objects,meta)
    letter_zones(objects,letters,names)
    for o in objects:
        if o.get('_type')==15:assert o['ZoneIcon']==ord(o['_dname'][0])-ord('A')+1,o['_dname']
    assert head['spz']==next(o['_uid'] for o in objects if o.get('_type')==7),'one active play area expected'
    assert sum(1 for o in objects if o.get('_type')==18)==2,'two team cameras expected'
    deployment(nodes)
    slider_defaults(objects,meta,2)
    return head,nodes,objects,meta
def deployment(nodes):
    """The deployment pause of an authored online script: (start, pause, wait, unpause, wire from unpause)."""
    byid={b['id']:b for b in nodes['b']}
    def val(b,k):return next(p['v'] for p in b['props_v2'] if p['k']==k)
    start=[b['id'] for b in nodes['b'] if b['nnKey']=='start'];assert len(start)==1,start
    pause={val(b,'val'):b['id'] for b in nodes['b'] if b['nnKey']=='pauseGame'};assert len(pause)==2,pause
    on,off=pause['True'],pause['False']
    wait=[c['b'] for c in nodes['c'] if c['a']==off and byid[c['b']]['nnKey']=='delay'];assert len(wait)==1,wait
    assert {(c['a'],c['b']) for c in nodes['c'] if c['b']==start[0]}>={(on,start[0]),(wait[0],start[0])}
    assert val(byid[wait[0]],'Time')==str(deploy_seconds())
    after=[c for c in nodes['c'] if c['b']==off];assert len(after)==1,after
    return start[0],on,wait[0],off,after[0]
def build_authored(out,spec,base):
    for flavor in spec['flavors']:
        head,nodes,objects,meta=copy.deepcopy(base)
        if flavor['kind']==3:
            start,on,wait,off,after=deployment(nodes)
            gone={on,wait,off}
            nodes['b']=[b for b in nodes['b'] if b['id'] not in gone]
            nodes['c']=[c for c in nodes['c'] if c['a'] not in gone and c['b'] not in gone]
            nodes['c'].append(dict(a=after['a'],b=start,c=after['c'],d='flow',e=start))
            set_bots(objects,meta)
        write_flavor(out,spec,flavor,head,objects,nodes,meta)
def authored_flavors(name,skirmish_name):
    return [dict(name=name,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,name)),kind=2,public=True),
            dict(name=skirmish_name,guid=str(uuid.uuid5(uuid.NAMESPACE_URL,skirmish_name)),kind=3,public=False)]
# Map batch: orient authored spawns and starting cameras using each team's own spawn side.
def face_spawns_to_objectives(objects,team=None):
    import math
    zones=[o['pos'] for o in objects if o.get('_type')==15]
    cx=sum(p['X'] for p in zones)/len(zones);cz=sum(p['Z'] for p in zones)/len(zones)
    for o in objects:
        if o.get('_type')!=10 or (team is not None and o['team']['id']!=team):continue
        half=math.atan2(cx-o['pos']['X'],cz-o['pos']['Z'])/2
        o['rotate']=dict(X=0.0,Y=math.sin(half),Z=0.0,W=math.cos(half))
def add_team_cameras(objects,ground=False):
    """One start camera per team over the middle of its spawns, looking 1200 m toward the centre of the zones.
    ground: use only the ground spawns, spawn type 1 (End 27 Nov 2026: "the starting camera location between their two respective ground spawns");
    helicopter-only (4) and air (5) spawns are left out."""
    import math
    assert not any(o.get('_type')==18 for o in objects),'Existing cameras need explicit reconciliation'
    zones=[o['pos'] for o in objects if o.get('_type')==15]
    cx=sum(p['X'] for p in zones)/len(zones);cz=sum(p['Z'] for p in zones)/len(zones)
    for team,name in [('Alpha team','Camera alpha'),('Bravo team','Camera bravo')]:
        tid=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']==team)
        ps=[o['pos'] for o in objects if o.get('_type')==10 and o['team']['id']==tid and not (ground and 1 not in o.get('spawnType2',[]))]
        assert ps,team
        x=sum(p['X'] for p in ps)/len(ps);z=sum(p['Z'] for p in ps)/len(ps);y=sum(p['Y'] for p in ps)/len(ps)
        d=math.hypot(cx-x,cz-z);assert d>1200,team
        add_camera(objects,team,name,dict(X=x,Y=y,Z=z),dict(X=x+(cx-x)*1200/d,Y=y,Z=z+(cz-z)*1200/d),700)
