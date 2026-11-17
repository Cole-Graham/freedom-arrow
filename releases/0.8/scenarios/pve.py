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
       1136:(1,[]),1146:(1,[]),1257:(0,[]),1268:(2,[]),1139:(1,[]),1083:(2,[(2019401,31101)]),925:(3,[]),1143:(1,[]),906:(2,[]),1137:(1,[]),
       # AI purchase cards (default loadouts): aircraft ucat 6, helicopters 5
       943:(6,[(2016862,24458)]),975:(6,[(2016971,24479)]),1092:(6,[(2016997,24483)]),1270:(5,[(2019263,31085)]),1041:(3,[]),
       917:(6,[(2016532,24398)]),955:(6,[(2016601,24406)]),1242:(6,[(2016697,24420)]),1103:(5,[(2017279,24523)]),1033:(3,[]),
       923:(6,[(2016794,24442)]),916:(6,[(2016642,24412)]),924:(6,[(2016825,24450)]),913:(5,[(2017056,24493)]),1040:(3,[])}
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
# With the Lua AI: only the first wave is fixed (the opening deployment); after that the AI buys its own units. Cards it can buy, one per
# kind, each purchase = that card x number of players. ba_purchase.lua channel 1 (inputs 1-5): fighter, strike, bomber, attack helicopter,
# ground seed (rebuild when wiped out); channel 2: air defence, artillery, infantry, recon, main armour, picked by BA_MIND.scorePurchase
# from what the enemy fields and what it already has. Card cooldowns as a player's; at most AI_MAX_UNITS x players live units.
AI_CARDS={
 'Dead Center':dict(ch1=[943,975,1092,1270,1175],ch2=[1051,1041,1192,1258,1061]),   # J-15, J-8D, J-7, Z-10U, Infantry | PGZ-88, PLZ-83, Marines, ZBD-86 Recon, ZTZ-80
 'Highway of Death':dict(ch1=[917,955,1242,1103,1196],ch2=[1052,1033,1196,1201,1082]),  # J-10C, J-10S, J-11D, Z-19, Moto. Riflemen | PGZ-95, PCL-09, Moto. Riflemen, Recon Patrol, ZTZ-96A
 'Dam':dict(ch1=[923,916,924,913,1136],ch2=[925,1040,1136,1257,1083])}              # J-11BS, J-16, Su-30MKK, Z-10K, Airborne | HQ-7B, PLZ-70, Airborne, ZBD-03 Recon, ZTZ-99
AI_MAX_UNITS=14
def opening(waves):
    """The AI's opening deployment, as a player's first buy: waves 1 and 2 together, 1 minute after the deployment pause."""
    merged={}
    for _,c in waves[:2]:
        for u,n in c.items():merged[u]=merged.get(u,0)+n
    return [(1,merged)]

# ---- Lua decision AI (Osama 13:2x PST: "we should be using real AI", "Plug it into all of them but make sure they fast move and use roads").
# BrokenArrowAI (seaborndan/BrokenArrowAI 4e4e6450, the pinned checkout on the deck; NOT copied into this repo, see LICENSE NOTE) commands the
# China units: it reads the battlefield every few seconds, picks objectives, supports, flanks, pulls damaged units back and moves on roads
# (MoveToFast) for anything further than FAST_MOVE_MIN, attack-moving the last leg. The waves above stay as its reinforcements; the scripted
# capture/escort orders are left out when the AI is in, so two commanders never fight over one unit. Terrain (cover, chokepoints, overwatch)
# comes from pve_terrain/ba_terrain_<scene>.lua, baked from the game's Navigation files by its tools/bake_terrain.py.
# Changes to the pinned source, applied here so the checkout stays pristine:
# - commanders: the Bravo players (the empty, locked Bravo slots online; Bravo bots offline), instead of IsBot only;
# - FAST_MOVE_MIN 700 -> 400 m, so more moves use the roads.
# LICENSE NOTE: the repository has no licence file; ask the author before shipping it outside the team.
import os
AI_SRC=Path(os.environ.get('FA_PVE_AI_SRC','/home/sam/tars/work/ba-dev/replicas/codex/work/ba-tool-verification-20261102/toolkit/sources/BrokenArrowAI'))
AI_FILES=['ba_tactics.lua','ba_roles.lua','ba_doctrine.lua','ba_field.lua','ba_mind.lua','ba_brain.lua']
TERRAIN=Path(__file__).resolve().parent/'pve_terrain'
def ai_code(scene):
    """One Lua chunk: PvE flag + baked terrain + the AI modules + the commander (tools/deploy_lua.py order)."""
    parts=['BA_FA_PVE = true   -- Freedom Arrow PvE: the AI commands the Bravo players',
           (TERRAIN/f"ba_terrain_{scene.replace(' ','_')}.lua").read_text(encoding='utf-8')]
    parts+=[(AI_SRC/'ai'/f).read_text(encoding='utf-8') for f in AI_FILES]
    code='\n'.join(parts)
    old_cond="    if safe(function() return p.IsBot end, false) then\n      local uid = safe(function() return p.UID end)"
    # The Bravo players: online they are empty, locked slots (IsBot false, no human), offline they are bots. LuaPlayer.TeamName is the team
    # object's name ("Bravo team" in every FA map); TeamID 1 = TeamSide.Bravo is the fallback.
    new_cond=("    local fa_bravo = string.find(tostring(safe(function() return p.TeamName end, '')), 'Bravo', 1, true) ~= nil\n"
              "                     or safe(function() return p.TeamID end, -1) == 1\n"
              "    if (BA_FA_PVE and fa_bravo) or (not BA_FA_PVE and safe(function() return p.IsBot end, false)) then\n"
              "      local uid = safe(function() return p.UID end)")
    for a,b in ((old_cond,new_cond),('  FAST_MOVE_MIN   = 700,','  FAST_MOVE_MIN   = 400,')):
        assert code.count(a)==1,('BrokenArrowAI changed: '+a[:40]);code=code.replace(a,b)
    return code
def pve_header(objects,players):
    bravo=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']=='Bravo team')
    sp=[o['pos'] for o in objects if o.get('_type')==10 and o['team']['id']==bravo and 5 not in o.get('spawnType2',[])]
    spawns=', '.join(f"{{x={q['X']:.1f}, y={q['Y']:.1f}, z={q['Z']:.1f}}}" for q in sp)
    return f'''BA_FA_PVE = true   -- Freedom Arrow PvE: the AI commands and buys for the Bravo players
BA_FA_MAX_UNITS = {AI_MAX_UNITS*players}
BA_FA_SPAWNS = {{ {spawns} }}   -- Bravo ground spawns: purchases arrive here, as a player's do
local fa_pick = 0
function FA_SPAWN()
  fa_pick = fa_pick % #BA_FA_SPAWNS + 1
  local s = BA_FA_SPAWNS[fa_pick]
  return Vectors.CreateVector3(s.x, s.y, s.z)
end
local function fa_isbravo(p)
  local ok, n = pcall(function() return p.TeamName end)
  if ok and n ~= nil and string.find(tostring(n), 'Bravo', 1, true) ~= nil then return true end
  local ok2, t = pcall(function() return p.TeamID end)
  return ok2 and t == 1
end
function FA_IS_BRAVO(uid)
  local ok, ps = pcall(function() return API.GetAllPlayers() end)
  if not ok or ps == nil then return false end
  for _, p in pairs(ps) do
    local ok2, u = pcall(function() return p.UID end)
    if ok2 and u == uid then return fa_isbravo(p) end
  end
  return false
end
-- Budget parity: the richest human's current money.
function FA_HUMAN_MONEY()
  local ok, ps = pcall(function() return API.GetAllPlayers() end)
  if not ok or ps == nil then return 0 end
  local best = 0
  for _, p in pairs(ps) do
    if not fa_isbravo(p) then
      local ok2, m = pcall(function() return p:GetMoney() end)
      if ok2 and type(m) == 'number' and m > best then best = m end
    end
  end
  return best
end
-- The owner of the spawned units: "Bravo Player 1" (the map's spawn nodes use it), else the lowest Bravo UID.
function FA_BRAVO_UID()
  local ok, ps = pcall(function() return API.GetAllPlayers() end)
  if not ok or ps == nil then return nil end
  local best = nil
  for _, p in pairs(ps) do
    if fa_isbravo(p) then
      local ok2, u = pcall(function() return p.UID end)
      local ok3, nm = pcall(function() return p.PlayerName end)
      if ok3 and nm == 'Bravo Player 1' and ok2 then return u end
      if ok2 and u ~= nil and (best == nil or u < best) then best = u end
    end
  end
  return best
end
'''
PURCHASE_FILES=['ba_tactics.lua','ba_roles.lua','ba_doctrine.lua','ba_field.lua','ba_mind.lua','ba_purchase.lua']
def purchase_code(scene,header):
    parts=[header,(TERRAIN/f"ba_terrain_{scene.replace(' ','_')}.lua").read_text(encoding='utf-8')]
    parts+=[(AI_SRC/'ai'/f).read_text(encoding='utf-8') for f in PURCHASE_FILES]
    code='\n'.join(parts)
    for a,b in (('local function rallyPoint(units)\n','local function rallyPoint(units)\n  if BA_FA_SPAWNS ~= nil then return FA_SPAWN() end\n'),
                ('local function fallbackDrop(uid)\n','local function fallbackDrop(uid)\n  if BA_FA_SPAWNS ~= nil then return FA_SPAWN() end\n'),
                ('local function ownerUID(slot)\n','local function ownerUID(slot)\n  if BA_FA_PVE then return FA_BRAVO_UID() end\n'),
                ('local function isBotUID(uid)\n','local function isBotUID(uid)\n  if BA_FA_PVE then return FA_IS_BRAVO(uid) end\n'),
                ('  MAX_UNITS   = 26,','  MAX_UNITS   = BA_FA_MAX_UNITS or 26,'),
                # Upstream bug: tick() calls situation() before its `local function` line, so with ba_field/ba_mind loaded (the deploy
                # order its README uses) channel 1 hit a nil global and never bought. Measured with its own test_purchase.lua: 9 of 24 fail
                # with field+mind loaded, all 24 pass with this forward declaration.
                ('local function tick(slot)','local situation   -- forward declaration (see pve.py)\nlocal function tick(slot)'),
                ('local function situation(uid, team, units)','situation = function(uid, team, units)'),
                # Budget parity (the toolkit's own principle): the empty Bravo slot has no money, so channel 2 would rate every card
                # unaffordable. In PvE it is rated against the richest human's money instead; spending is still capped by the purchase
                # interval, card cooldowns and BA_FA_MAX_UNITS.
                ('  ctx.money = (type(money) == "number") and money or 0','  ctx.money = (type(money) == "number") and money or 0\n  if BA_FA_PVE then ctx.money = FA_HUMAN_MONEY() end')):
        assert code.count(a)==1,('BrokenArrowAI ba_purchase changed: '+a[:40]);code=code.replace(a,b)
    return code
def add_purchase(nodes,objects,scene,players,cards):
    """Two buying channels for BP1 (ba_purchase.lua Buy_BP1 / Buy2_BP1), wired as tools/inject_purchase.py does: start -> looped LuaNode,
    static payloads on input_1..5, output_1 -> spawn.UnitInfo, output_2 -> spawn.targetVec, out -> spawn.in, error -> self."""
    owner=next(o['_uid'] for o in objects if o.get('_type')==13 and o['_dname']=='Bravo Player 1')
    start=[b['id'] for b in nodes['b'] if b['nnKey']=='start'][0]
    code=purchase_code(scene,pve_header(objects,players))
    nid=max(b['id'] for b in nodes['b'])+500
    def node(key,props,x,y):
        nonlocal nid;nid+=1;nodes['b'].append({'v':0,'nnKey':key,'px':x,'py':y,'id':nid,'rtpt':True,'props_v2':props});return nid
    def wire(a,c,b,d):nodes['c'].append({'a':a,'b':b,'c':c,'d':d,'e':b})
    player=node('node_player',[p('value',f'c{owner}')],-3400.0,8000.0)
    store=node('mission_storage',[p('value','BP1'),p('actOnSt','False')],-3000.0,8000.0);wire(store,'in',player,'out')
    for k,(enter,ids) in enumerate((('Buy_BP1',cards['ch1']),('Buy2_BP1',cards['ch2']))):
        y=8300.0+k*600.0
        lua=node('LuaNode',[p('EnterMethod',enter),p('Loop','True'),p('Code',code),p('hotreload','False')],-2600.0,y)
        wire(lua,'in',start,'flow');wire(lua,'in',lua,'error')
        for i,uid in enumerate(ids):
            data=node('getSpMultUnData',[p('val',payload({uid:1},players))],-3000.0,y+100+i*60);wire(lua,f'input_{i+1}',data,'out')
        spawn=node('spawnMultiUnits',[p('TargetTag','',1),p('TargetSpawnPoint','',1),p('PlayerOwner','c0',1),p('UnitInfo','',1),
                                      p('UnitGroup',f'FAPVEBUY{k+1}'),p('CargoUnitGroup',f'FAPVEBUY{k+1}C'),p('assign','False')],-2000.0,y)
        wire(spawn,'UnitInfo',lua,'output_1');wire(spawn,'targetVec',lua,'output_2');wire(spawn,'in',lua,'out');wire(spawn,'PlayerOwner',player,'out')

def add_ai(nodes,scene):
    """start.flow -> LuaNode(AiTick, looped, code embedded so no file path is needed); its error output re-enters it."""
    start=[b['id'] for b in nodes['b'] if b['nnKey']=='start'];assert len(start)==1,start
    nid=max(b['id'] for b in nodes['b'])+1
    nodes['b'].append({'v':0,'nnKey':'LuaNode','px':-3000.0,'py':3600.0,'id':nid,'rtpt':True,'props_v2':[
        p('EnterMethod','AiTick'),p('Loop','True'),p('Code',ai_code(scene)),p('hotreload','False')]})
    nodes['c'].append({'a':nid,'b':start[0],'c':'in','d':'flow','e':start[0]})
    nodes['c'].append({'a':nid,'b':nid,'c':'in','d':'error','e':nid})
    return nid

def payload(counts,players):
    units=[]
    for uid,n in counts.items():
        ucat,items=UNITS[uid]
        for _ in range(n*players):
            units.append({'unitId':uid,'ucat':ucat,'items':[{'mod':m,'opt':o} for m,o in items],'skin':0,
                          'cargo':{'totals':0,'taken':0,'totalHL':0,'takenHL':0,'cargos':[],'supply':0}})
    return json.dumps({'Units':units,'TotalUnitsCount':len(units)},separators=(',',':')).replace('"','¨')

def p(k,v,t=3):return {'k':k,'v':v,'t':t}

# Doctrine (Osama 13:2x PST: "make sure the AI are pre programmed with a smart strategy", "It should play like a PVP game and get players ready
# for pvp"). Each wave is split by role into its own group, the way a player uses combined arms:
# - recon (ucat 0): takes the nearest open zone first and stays there as a forward screen;
# - infantry (ucat 1, and recon infantry): takes a zone and holds it for HOLD_SECONDS, then takes the next;
# - armour (ucat 2): overwatch: every 20 s it attack-moves to its infantry; with no infantry left it spearheads zone to zone itself;
# - air defence (ucat 3): escorts the armour every 15 s (the infantry when no armour is left).
# Scripted, not adaptive: no retreat, no artillery fire missions, no aircraft yet.
HOLD_SECONDS=120
INF_RECON={1201}   # Recon Patrol: infantry that scouts, moves with the infantry group
def role(uid):
    ucat=UNITS[uid][0]
    return 'I' if ucat==1 or uid in INF_RECON else {0:'R',2:'A',3:'S'}[ucat]

def add_waves(nodes,objects,players,after,waves,orders=True):
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
    def delay(sec,x,y):return node('delay',[p('Time',str(sec),1),p('igGmSp','False',1)],x,y)
    def capture(group,x,y):
        return node('captureObj',[p('tgz2','c-2',1),p('AggressiveRadius2','600:0:0',1),p('forUnit2','c0'),p('forGroup2',group),p('pathf','Fast'),
                                  p('moveAttack','True'),p('lt','60'),p('bl','True')],x,y)
    def follow(group,leader,radius,x,y):
        """getObjPos(leader centre) -> moveComplex(group, attack-move). Returns (position node, move node)."""
        pos=node('getObjPos',[p('forGroup',leader),p('center','True')]+[p(k,'c0') for k in ('targetUnitLink','targetTriggerLink','targetTagLink',
                 'targetZoneLink','targetWayLink','targetSPLink')],x,y)
        mv=node('moveComplex',[p('tt2','c0',1),p('AggressiveRadius2',f'{radius}:0:0',1),p('forUnit2','c0'),p('forGroup2',group),p('pathf','Fast'),
                p('moveAttack','True'),p('speedLimit','True'),p('tranBeh','LoadInTransport'),p('duringRide','UnloadWhenEngaged'),p('atDest','Nothing'),
                p('ErrorRadius','80'),p('lt','-1'),p('bl','True')],x+400,y)
        wire(mv,'targetVec3',pos,'outPos');wire(mv,'in2',pos,'outFound')
        return pos,mv
    player=node('node_player',[p('value',f'c{owner}')],-3000.0,4000.0)
    prev,prev_port,t=after[0],after[1],0
    for i,(minute,counts) in enumerate(waves):
        y=4300.0+i*1200.0;g=f'FAPVE{i+1}'
        wait=delay((minute-t)*60,-3000.0,y);t=minute;wire(wait,'in2',prev,prev_port)
        go=delay(1,-2700.0,y);wire(go,'in2',wait,'out2')
        roles={}
        for u,n in counts.items():roles.setdefault(role(u),{})[u]=n
        tag=node('getTag',[p('val',f'c{tags[i%len(tags)]}')],-2400.0,y-150)
        settled={}
        for k,(r,c) in enumerate(sorted(roles.items())):
            yy=y+k*250.0
            data=node('getSpMultUnData',[p('val',payload(c,players))],-2400.0,yy+100)
            spawn=node('spawnMultiUnits',[p('TargetTag','c0',1),p('TargetSpawnPoint','c0',1),p('PlayerOwner','c0',1),p('UnitInfo','',1),
                                          p('UnitGroup',g+r),p('CargoUnitGroup',g+r+'C'),p('assign','False')],-2000.0,yy)
            wire(spawn,'in',go,'out2');wire(spawn,'UnitInfo',data,'out');wire(spawn,'TargetTag',tag,'out');wire(spawn,'PlayerOwner',player,'out')
            settled[r]=delay(3,-1600.0,yy);wire(settled[r],'in2',spawn,'out')
        x=-1200.0
        if not orders:prev,prev_port=wait,'out2';continue   # the Lua AI gives the orders
        if 'R' in settled:   # recon: one zone, then stay as a screen
            cap=capture(g+'R',x,y);wire(cap,'in2',settled['R'],'out2')
            retry=delay(30,x+400,y);wire(retry,'in2',cap,'outFailed');wire(cap,'in2',retry,'out2')
        if 'I' in settled:   # infantry: take a zone, hold it, take the next
            cap=capture(g+'I',x,y+250);wire(cap,'in2',settled['I'],'out2')
            hold=delay(HOLD_SECONDS,x+400,y+250);wire(hold,'in2',cap,'out2');wire(cap,'in2',hold,'out2')
            retry=delay(30,x+400,y+350);wire(retry,'in2',cap,'outFailed');wire(cap,'in2',retry,'out2')
        if 'A' in settled:   # armour: overwatch on its infantry, else spearhead
            tick=delay(20,x,y+500);wire(tick,'in2',settled['A'],'out2')
            if 'I' in settled:
                pos,mv=follow(g+'A',g+'I',500,x+400,y+500)
                wire(pos,'in',tick,'out2');wire(tick,'in2',mv,'out2');wire(tick,'in2',mv,'outFailed')
                lead=capture(g+'A',x+1200,y+500);wire(lead,'in2',pos,'outMiss')
            else:
                lead=capture(g+'A',x+400,y+500);wire(lead,'in2',tick,'out2')
            wire(tick,'in2',lead,'out2');wire(tick,'in2',lead,'outFailed')
        if 'S' in settled:   # air defence: escort the armour, else the infantry
            leader=g+'A' if 'A' in settled else g+'I' if 'I' in settled else None
            tick=delay(15,x,y+750);wire(tick,'in2',settled['S'],'out2')
            if leader:
                pos,mv=follow(g+'S',leader,300,x+400,y+750)
                wire(pos,'in',tick,'out2');wire(tick,'in2',mv,'out2');wire(tick,'in2',mv,'outFailed');wire(tick,'in2',pos,'outMiss')
            else:
                lead=capture(g+'S',x+400,y+750);wire(lead,'in2',tick,'out2');wire(tick,'in2',lead,'out2');wire(tick,'in2',lead,'outFailed')
        prev,prev_port=wait,'out2'
    # The last wave again every REPEAT_MINUTES (scripted mode only; the Lua AI buys its own reinforcements).
    if orders:
        loop=delay(REPEAT_MINUTES*60,-3000.0,4300.0+len(waves)*1200.0)
        wire(loop,'in2',go,'out2');wire(go,'in2',loop,'out2')
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
    settings=C.settings();ai=(AI_SRC/'ai'/'ba_brain.lua').exists()
    print('PvE commander:','BrokenArrowAI Lua' if ai else f'scripted orders ({AI_SRC} not found)')
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
                waves=add_waves(n,o,players,(start[0],'flow'),opening(WAVES[title]) if ai else WAVES[title],orders=not ai)
                if ai:add_ai(n,h['map']);add_purchase(n,o,h['map'],players,AI_CARDS[title])   # the base Skirmish flavor: bots, no deployment pause
            else:
                # Waves start when the deployment pause ends: the delay that unpauses the game.
                off=[b['id'] for b in n['b'] if b['nnKey']=='pauseGame' and any(q['k']=='val' and q['v']=='False' for q in b['props_v2'])];assert len(off)==1,off
                wait=[c['b'] for c in n['c'] if c['a']==off[0] and c['d']=='out2'];assert len(wait)==1,wait
                waves=add_waves(n,o,players,(wait[0],'out2'),opening(WAVES[title]) if ai else WAVES[title],orders=not ai)
                if ai:add_ai(n,h['map']);add_purchase(n,o,h['map'],players,AI_CARDS[title])
                configure_slots(o,m,players)
            C.check_spawns(flavor,h,o)
            C.check_limit(flavor,desc)
            C.stamp(h,m,flavor,str(uuid.uuid5(uuid.NAMESPACE_URL,flavor)),desc,'Freedom Arrow',kind,kind==2)
            C.write(out,flavor,h,o,n,m)
            print(f'{flavor}: {waves[0]} waves from {waves[1]} Bravo spawns, {players} human slot(s)')
