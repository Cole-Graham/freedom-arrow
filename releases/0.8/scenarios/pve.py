"""[FA] [PvE] maps (Osama 17 Nov 2026 13:0x-13:1x PST, thread 1571014792016171120): "a multiplayer scenario that has bots in it and people are
playing PVE against the Bots ... everyone joins one team", "it's a preset scenario", "option 1 add a section to our map selection that is PVE",
"make an AI PVE 1v1 2v2 and 3v3 scenario? Fighting China".

Each PvE map is an existing FA map: 1, 2 or 3 open human slots on Alpha, every other slot locked, no bot slots (so the lobby has no bot and
ArrowQueue's "AI bot in the lobby" warning does not apply). The map script spawns China waves for Bravo Player 1 at Bravo's ground spawns and
sends each wave to capture zones on roads, again and again; waves grow with time and with the number of players. Scoring is the normal FA
conquest. Script shape copied from vanilla Dam_Skirmish: node_player -> spawnMultiUnits.PlayerOwner, getSpMultUnData -> UnitInfo,
getTag (a type-6 tag object) -> TargetTag, then captureObj (tgz2 c-2, pathf Fast, moveAttack) for the wave's UnitGroup.
Open question, to be tested: whether units can be spawned for a locked, empty Bravo slot in an online lobby. The Skirmish flavor (offline
test) has bots as in every FA Skirmish flavor; LocalSkirmish leaves FAPVE* groups as designed.
"""
import copy, json, shutil, tempfile, uuid
from pathlib import Path
import common as C
import dead_center_1v1, highway_2v2, dam_3v3

# (players, base module, online base name, title, enemy specializations). Osama 13:2x PST: "I want to make sure as many specs are played in these
# scenarios. Dead center should be SF rocket". Every China specialization fights on at least one map. The base's zone weights are copied to the
# PvE names (settings.json MapZoneWeights).
BASES=[(1,dead_center_1v1,dead_center_1v1.NAME,'Dead Center','PLAN Special Forces + PLARF Rocket Conscript Force'),
       (2,highway_2v2,highway_2v2.NAME,'Highway of Death','PLAGF Motorized + PLAGF Armored Force'),
       (3,dam_3v3,dam_3v3.NAME,'Dam','PLAAF Air Force (airborne) + PLAGF Armored Force')]
def names(players,title):
    n=f'[FA] [PvE] {title} vs China ({players}P) 0.1';return n,n.replace(' 0.1',' Skirmish 0.1')
ALL_NAMES=[x for p,_,_,t,_ in BASES for x in names(p,t)]

# China units of those specializations, default options (0.9.0-dev.36 data): unitId -> (ucat = CategoryType, [(modification, option)]).
# Ground only: the waves are capture orders, which aircraft and artillery do not fly or fire well. queued_checks.py checks every id per build.
UNITS={1166:(1,[]),1175:(1,[]),1172:(1,[]),1183:(1,[]),1192:(1,[]),1181:(1,[]),1258:(0,[(2018888,31053)]),1060:(2,[]),1061:(2,[]),
       1272:(2,[]),1261:(2,[]),909:(3,[]),1051:(3,[]),
       1205:(1,[]),1201:(0,[]),1059:(2,[]),1196:(1,[]),938:(2,[]),1163:(1,[]),1082:(2,[]),1080:(2,[(2019214,31077)]),1052:(3,[]),
       904:(2,[(2019383,31098)]),905:(2,[]),1198:(1,[]),1049:(3,[]),
       1136:(1,[]),1146:(1,[]),1257:(0,[]),1268:(2,[]),1139:(1,[]),1083:(2,[(2019401,31101)]),925:(3,[]),1143:(1,[]),906:(2,[]),1137:(1,[])}
# Waves for one player (unitId: count); counts are multiplied by the number of players. Minute = after the deployment pause. The last wave
# repeats every REPEAT_MINUTES.
WAVES={
 'Dead Center':[(1,{1166:2,1258:1}),                                   # Conscripts, ZBD-86 Recon
                (4,{1175:2,1172:1,1060:1}),                            # Infantry, PF-98 Team, ZTZ-59
                (7,{1192:2,1061:2,1051:1}),                            # Marines, ZTZ-80, PGZ-88
                (10,{1183:1,1181:1,1261:1,1272:1,909:1})],             # Blood Wolves, Godswords, VT-5, WZ1224, PGZ-09
 'Highway of Death':[(1,{1205:2,1201:1,1059:1}),                       # Light Riflemen, Recon Patrol, PTL-02
                     (4,{1196:2,1163:1,938:1}),                        # Moto. Riflemen, Mech. Rifles, ZTL-11
                     (7,{1082:2,1080:1,1052:1}),                       # ZTZ-96A, ZTL-191, PGZ-95
                     (10,{904:1,905:1,1198:2,1049:1})],                # ZTZ-99A, ZTZ-96B, AT Troopers, HQ-17A
 'Dam':[(1,{1136:1,1146:1,1257:1}),                                    # Airborne, Assault Raiders, ZBD-03 Recon
        (4,{1163:2,1139:1,1268:1}),                                    # Mech. Rifles, Tank Hunters, ZTQ-15 Light
        (7,{1082:1,1083:1,1143:1,925:1}),                              # ZTZ-96A, ZTZ-99, Thunder Gods, HQ-7B
        (10,{904:1,905:1,906:1,1137:1,1052:1})]}                       # ZTZ-99A, ZTZ-96B, ZTQ-15, HJ-12 Team, PGZ-95
REPEAT_MINUTES=3

def payload(counts,players):
    units=[]
    for uid,n in counts.items():
        ucat,items=UNITS[uid]
        for _ in range(n*players):
            units.append({'unitId':uid,'ucat':ucat,'items':[{'mod':m,'opt':o} for m,o in items],'skin':0,
                          'cargo':{'totals':0,'taken':0,'totalHL':0,'takenHL':0,'cargos':[],'supply':0}})
    return json.dumps({'Units':units,'TotalUnitsCount':len(units)},separators=(',',':')).replace('"','¨')

def p(k,v,t=3):return {'k':k,'v':v,'t':t}

def add_waves(nodes,objects,players,after,waves):
    """after = (node id, out port) that fires when the deployment pause ends."""
    bravo=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']=='Bravo team')
    owner=next(o['_uid'] for o in objects if o.get('_type')==13 and o['_dname']=='Bravo Player 1')
    spawns=[o for o in objects if o.get('_type')==10 and o['team']['id']==bravo and 5 not in o.get('spawnType2',[])]
    assert spawns,'no Bravo ground spawn'
    uid=C.new_uid(objects);tags=[]
    for i,s in enumerate(spawns):
        objects.append({'info':'','noArrow':False,'color':0,'pos':copy.deepcopy(s['pos']),'rotate':copy.deepcopy(s['rotate']),
                        'scale':{'X':1.0,'Y':1.0,'Z':1.0,'SqrMagnitude':3.0},'v':1,'_uid':uid+i,'_type':6,'_dname':f'PVE spawn {i+1}'})
        tags.append(uid+i)
    nid=max(b['id'] for b in nodes['b'])+1000
    def node(key,props,x,y):
        nonlocal nid;nid+=1;nodes['b'].append({'v':0,'nnKey':key,'px':x,'py':y,'id':nid,'rtpt':True,'props_v2':props});return nid
    def wire(a,c,b,d):nodes['c'].append({'a':a,'b':b,'c':c,'d':d,'e':b})
    player=node('node_player',[p('value',f'c{owner}')],-3000.0,4000.0)
    prev,prev_port,t=after[0],after[1],0
    for i,(minute,counts) in enumerate(waves):
        y=4300.0+i*400.0;group=f'FAPVE{i+1}'
        wait=node('delay',[p('Time',str((minute-t)*60),1),p('igGmSp','False',1)],-2600.0,y);t=minute
        wire(wait,'in2',prev,prev_port)
        data=node('getSpMultUnData',[p('val',payload(counts,players))],-2200.0,y+150)
        tag=node('getTag',[p('val',f'c{tags[i%len(tags)]}')],-2200.0,y+250)
        spawn=node('spawnMultiUnits',[p('TargetTag','c0',1),p('TargetSpawnPoint','c0',1),p('PlayerOwner','c0',1),p('UnitInfo','',1),
                                      p('UnitGroup',group),p('CargoUnitGroup',group+'C'),p('assign','False')],-1800.0,y)
        wire(spawn,'in',wait,'out2');wire(spawn,'UnitInfo',data,'out');wire(spawn,'TargetTag',tag,'out');wire(spawn,'PlayerOwner',player,'out')
        settle=node('delay',[p('Time','3',1),p('igGmSp','False',1)],-1400.0,y);wire(settle,'in2',spawn,'out')
        cap=node('captureObj',[p('tgz2','c-2',1),p('AggressiveRadius2','600:0:0',1),p('forUnit2','c0'),p('forGroup2',group),p('pathf','Fast'),
                               p('moveAttack','True'),p('lt','60'),p('bl','True')],-1000.0,y)
        wire(cap,'in2',settle,'out2')
        again=node('delay',[p('Time','20',1),p('igGmSp','False',1)],-600.0,y)   # zone taken or failed: wait, then take the next one
        wire(again,'in2',cap,'out2');wire(again,'in2',cap,'outFailed');wire(cap,'in2',again,'out2')
        prev,prev_port=wait,'out2'
    # The last wave again every REPEAT_MINUTES: its delay re-arms itself after each spawn.
    loop=node('delay',[p('Time',str(REPEAT_MINUTES*60),1),p('igGmSp','False',1)],-2600.0,4300.0+len(waves)*400.0)
    wire(loop,'in2',spawn,'out');wire(spawn,'in',loop,'out2')
    return len(waves),len(tags)

def configure_slots(objects,meta,players):
    """Alpha: the first `players` slots open; all others locked. No bots anywhere (the waves are the enemy)."""
    for t in meta['teams']:
        for i,s in enumerate(t['slots']):
            s['bot']=False;s['lock']=not(t['teamName']=='Alpha team' and i<players)
    open_names={s['playerName'] for t in meta['teams'] for s in t['slots'] if not s['lock']}
    for o in objects:
        if o.get('_type')==13:o['isBot']=False;o['lock']=o['_dname'] not in open_names
    assert len(open_names)==players,open_names

def build(game,out):
    settings=C.settings()
    for players,mod,base_name,title,enemy in BASES:
        name,skirmish=names(players,title)
        W=settings['MapZoneWeights'];assert W.get(name)==W[base_name] and W.get(skirmish)==W[mod.SKIRMISH_NAME],(name,'zone weights must equal those of',base_name)
        with tempfile.TemporaryDirectory() as tmp:
            mod.build(game,Path(tmp))
            base={k:C.read_bascr(Path(tmp)/nm,nm) for k,nm in ((2,base_name),(3,mod.SKIRMISH_NAME))}
        desc=(f'Freedom Arrow PvE: {players} player{"s" if players>1 else ""} on Alpha against China waves ({enemy}; map script AI, no bots in the lobby). '
              +base[2][0]['desc'])
        for flavor,kind in ((name,2),(skirmish,3)):
            h,n,o,m=copy.deepcopy(base[kind])
            if kind==3:
                start=[b['id'] for b in n['b'] if b['nnKey']=='start'];assert len(start)==1
                waves=add_waves(n,o,players,(start[0],'flow'),WAVES[title])   # the base Skirmish flavor: bots, no deployment pause
            else:
                # Waves start when the deployment pause ends: the delay that unpauses the game.
                off=[b['id'] for b in n['b'] if b['nnKey']=='pauseGame' and any(q['k']=='val' and q['v']=='False' for q in b['props_v2'])];assert len(off)==1,off
                wait=[c['b'] for c in n['c'] if c['a']==off[0] and c['d']=='out2'];assert len(wait)==1,wait
                waves=add_waves(n,o,players,(wait[0],'out2'),WAVES[title])
                configure_slots(o,m,players)
            C.check_spawns(flavor,h,o)
            C.check_limit(flavor,desc)
            C.stamp(h,m,flavor,str(uuid.uuid5(uuid.NAMESPACE_URL,flavor)),desc,'Freedom Arrow',kind,kind==2)
            C.write(out,flavor,h,o,n,m)
            print(f'{flavor}: {waves[0]} waves from {waves[1]} Bravo spawns, {players} human slot(s)')
