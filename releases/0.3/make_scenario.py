"""Build [FA] Central Village from the game's own Central Village_network mission."""
from pathlib import Path
import argparse, copy, hashlib, json, re, sys, zipfile
from Crypto.Cipher import AES
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parents[1]))
from pipeline.crypto import AES_KEY
MARKER=b'fhk3s0g3';NAME='[FA] Central Village';START_POINTS=1500;GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c003'
DESC=('Freedom Arrow conquest. Requires the Freedom Arrow mod on every player. Each 30 seconds, after a 5 minute Round 1 with no scoring, '
      'the side with the higher zone value scores the difference. First to 300 wins. A B G H I J are worth 4, C D are worth 3, E F are worth 2. Flat 200 income, no upkeep.')
SKIRMISH_NAME='[FA] Central Village Skirmish';SKIRMISH_GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c004'
GAME_VERSION='1.2.2'
MATCH_MINUTES=45
# Network scripts cap money at 1500. With 1500 starting points, income would stop until a player spends. Skirmish missions have no cap.
MONEY_CAP=100000
DEPLOY_SECONDS=60
ZONE_VALUES=dict(Alpha=4,Bravo=4,Charlie=3,Delta=3,Echo=2,Foxtrot=2,Golf=4,Hotel=4,India=4,Juliet=4)
# Lateralus's map, from maps/. A script added there later needs this step checked again.
DEAD_CENTER_MODE=136
DEAD_CENTER='[FA] Dead Center 0.1';DEAD_CENTER_GUID='6fa0c3d4-5b1e-4e0a-9b7c-0f4a3e21c005'
DEAD_CENTER_VALUES=dict(A=('Alpha',2),B=('Bravo',2),C=('Charlie',2),D=('Delta',3),E=('Echo',3))
DEAD_CENTER_DESC=DESC.replace('A B G H I J are worth 4, C D are worth 3, E F are worth 2.','A B C are worth 2, D E are worth 3.')
def dec(raw):
    assert raw[:8]==MARKER
    p=AES.new(AES_KEY,AES.MODE_CBC,raw[8:24]).decrypt(raw[24:]);return p[:-p[-1]]
def enc(p):
    # IV comes from the content, so the same input gives the same file on every build machine.
    iv=hashlib.sha256(p).digest()[:16];n=16-len(p)%16
    return MARKER+iv+AES.new(AES_KEY,AES.MODE_CBC,iv).encrypt(p+bytes([n])*n)
def load(b):return json.loads(b.decode('utf-8-sig'))
def dump(o):return json.dumps(o,indent=2,ensure_ascii=False).encode('utf-8')
def weights(name):return json.loads((R/'source/UserData/FAConquestPrototype/settings.json').read_text())['MapZoneWeights'][name]
def slider_defaults(objects,meta,want_money):
    # The lobby slider runs 500 to 1500. Default it to the top. Skirmish missions have no slider.
    money=[o for o in objects if o.get('desc')=='ui_lobby_StartMoney_desc']+[o for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_StartMoney_desc']
    assert len(money)==want_money
    for o in money:
        o['defV']=START_POINTS
        if 'tstV' in o:o['tstV']=START_POINTS
    # Both versions default to the same 45 minute match. Skirmish missions default to 30.
    timers=[o for o in objects if o.get('desc')=='ui_lobby_Timer_desc']+[o for o in meta['pblOpt'] if o.get('desc')=='ui_lobby_Timer_desc']
    assert len(timers)==2
    for o in timers:
        o['defV']=MATCH_MINUTES
        if 'tstV' in o:o['tstV']=MATCH_MINUTES
# Network deployment: pause at start, wait, unpause, then start the mode. Workshop [Flat 200] scenarios use these nodes online.
def add_deployment(nodes,start,target):
    wire={'a':target,'b':start,'c':'in','d':'flow','e':start}
    if target==DEAD_CENTER_MODE:wire['c']='in2'
    assert wire in nodes['c'],wire
    nodes['c'].remove(wire)
    assert not {n['nnKey'] for n in nodes['b']}&{'pauseGame'}
    first=max(n['id'] for n in nodes['b'])+1
    on,wait,off=first,first+1,first+2
    def node(i,key,props,x):return dict(v=0,nnKey=key,px=x,py=-900.0,id=i,rtpt=True,props_v2=[dict(k=k,v=v,t=1) for k,v in props])
    nodes['b']+=[node(on,'pauseGame',[('val','True')],-800.0),node(wait,'delay',[('Time',str(DEPLOY_SECONDS)),('igGmSp','True')],-500.0),node(off,'pauseGame',[('val','False')],-200.0)]
    nodes['c']+=[dict(a=on,b=start,c='in',d='flow',e=start),dict(a=wait,b=start,c='in2',d='flow',e=start),dict(a=off,b=wait,c='in',d='out2',e=wait),dict(a=target,b=off,c=wire['c'],d='out',e=off)]
def write(out,name,head,objects,nodes,meta):
    target=out/name;target.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(target/(name+'.bascr'),'w',zipfile.ZIP_DEFLATED) as w:
        for part,data in [('head.bam',dump(head)),('objects.bam',dump(objects)),('nodes.bam',dump(nodes))]:
            w.writestr(zipfile.ZipInfo(part,(2026,11,4,0,0,0)),enc(data),zipfile.ZIP_DEFLATED)
    (target/'meta.json').write_bytes(dump(meta))
    print(target)
def build(game,out,name,guid,mission,kind,desc,public):
    src=game/'BrokenArrow_Data/StreamingAssets/SharedMissions'/mission
    z=zipfile.ZipFile(src/(mission+'.bascr'));head=load(dec(z.read('head.bam')));nodes=load(dec(z.read('nodes.bam')));objects=load(dec(z.read('objects.bam')))
    assert head['GameMode']==kind and head['map']=='Central Village'
    # Scoring reads zone values by ID. Fail the build if the letters and IDs ever disagree.
    want={str(o['_uid']):ZONE_VALUES[o['hudText']] for o in objects if o.get('_type')==15}
    assert len(want)==len(ZONE_VALUES) and want==weights(name),want
    head.update(guid=guid,name=name,author='Freedom Arrow',desc=desc,IsDevVersion=False,devId=0,public=public)
    hits=shown=caps=0
    zones={f"c{o['_uid']}" for o in objects if o.get('_type')==15}
    for n in nodes['b']:
        if n.get('nnKey')=='setConquestMode':hits+=1
        # The small map size hides outer zones, and Auto picks small under 8 players. Every zone stays in FA.
        if n.get('nnKey')=='objVisible2':
            props={p['k']:p for p in n['props_v2']}
            if props['oz2']['v'] in zones and props['isv']['v']=='False':props['isv']['v']='True';shown+=1
        if n.get('nnKey')=='setIncomeCurveState':
            for p in n['props_v2']:
                if p['k']=='state':p['v']='False'
        if n.get('nnKey')=='setMaxMoney':
            next(p for p in n['props_v2'] if p['k']=='moneyValue')['v']=str(MONEY_CAP);caps+=1
    assert hits>=1,'scenario must use ConquestMode'
    assert caps==(1 if kind==2 else 0),caps
    assert shown==(4 if kind==2 else 5),shown
    meta=load((src/'meta.json').read_bytes());meta.pop('devid',None)
    # Skirmish scripts set starting money to 1000 times a team balance ratio, after the game default. Every player gets the FA value.
    calcs={c['b'] for c in nodes['c'] if c['d']=='Multiply' and c['c']=='amount' and any(b['id']==c['a'] and b.get('nnKey')=='setMoney2' for b in nodes['b'])}
    assert len(calcs)==(2 if kind==3 else 0),calcs
    byid={b['id']:b for b in nodes['b']}
    for calc in calcs:
        source=[c['b'] for c in nodes['c'] if c['a']==calc and c['c']=='a'];assert len(source)==1
        assert not [c for c in nodes['c'] if c['a']==source[0] and c['c']=='Value'],'money variable has an input'
        nodes['c']=[c for c in nodes['c'] if not (c['a']==calc and c['c']=='B')]
        next(p for p in byid[calc]['props_v2'] if p['k']=='B')['v']='1'
        next(p for p in byid[source[0]]['props_v2'] if p['k']=='Value')['v']=str(START_POINTS)
    slider_defaults(objects,meta,2 if kind==2 else 0)
    # 159 starts the mode selection in the network mission. F8 has its own freeze in the mod.
    if kind==2:add_deployment(nodes,163,159)
    # The game picks a database from the scenario's game version. The native 1.2.0 values do not load our tables.
    meta.update(guid=guid,scenario=name,author='Freedom Arrow',desc=desc,public=public,type=kind,gameVersion=GAME_VERSION)
    write(out,name,head,objects,nodes,meta)
# Dead Center has no script, so the game never starts ConquestMode and FA scoring cannot attach.
# Add the parts of the native script that matter here: FA money cap, no income curve, ConquestMode, and the three lobby sliders.
# Map size and daytime logic stay out. Lateralus's zones, spawns and playable zone do not move.
def build_dead_center(game,out):
    src=R.parents[1]/'maps'/DEAD_CENTER
    z=zipfile.ZipFile(src/(DEAD_CENTER+'.bascr'));head=load(dec(z.read('head.bam')));nodes=load(dec(z.read('nodes.bam')));objects=load(dec(z.read('objects.bam')));meta=load((src/'meta.json').read_bytes())
    assert head['GameMode']==2 and head['map']=='Central Village' and meta['gameVersion']==GAME_VERSION
    assert not nodes['b'] and not nodes['c'] and 'pblOpt' not in meta,'Dead Center has a script now. Check this merge.'
    zones=[o for o in objects if o.get('_type')==15]
    assert {o['_dname'] for o in zones}==set(DEAD_CENTER_VALUES) and {str(o['_uid']):DEAD_CENTER_VALUES[o['_dname']][1] for o in zones}==weights(DEAD_CENTER)
    teams={o['_dname']:o['_uid'] for o in objects if o.get('_type')==3}
    for o in zones:
        o['hudText']=DEAD_CENTER_VALUES[o['_dname']][0]
        # Native conquest zones list the two sides only.
        o['capturableBy']=[c for c in o['capturableBy'] if c['id'] in (teams['Alpha team'],teams['Bravo team'])];assert len(o['capturableBy'])==2
    mission='Central Village_network';native=game/'BrokenArrow_Data/StreamingAssets/SharedMissions'/mission
    n=zipfile.ZipFile(native/(mission+'.bascr'));nn=load(dec(n.read('nodes.bam')));no=load(dec(n.read('objects.bam')));nm=load((native/'meta.json').read_bytes())
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
    # The shipped Test_map_network uses this start to ConquestMode wire.
    wires.append(dict(a=136,b=163,c='in2',d='flow',e=163))
    nodes.update(b=script,c=wires)
    add_deployment(nodes,163,DEAD_CENTER_MODE)
    head.update(guid=DEAD_CENTER_GUID,desc=DEAD_CENTER_DESC)
    meta.update(guid=DEAD_CENTER_GUID,desc=DEAD_CENTER_DESC)
    write(out,DEAD_CENTER,head,objects,nodes,meta)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--game-dir',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    build(a.game_dir,a.out,NAME,GUID,'Central Village_network',2,DESC,True)
    # F8 Local AI lists Skirmish scenarios only, because PVP missions have no bot slots.
    build(a.game_dir,a.out,SKIRMISH_NAME,SKIRMISH_GUID,'Central_Village_Skirmish',3,DESC,False)
    build_dead_center(a.game_dir,a.out)
if __name__=='__main__':main()
