"""Interceptable missile HP test builds over exact 0.9.0-dev.12 (Lateralus, 15 Nov 2026, thread 1571554273639006392:
"give me three test builds that set the HP of all interceptables to 5, 7, and 9").

Each variant is dev.12 plus releases/0.6/source/runtime-qa/ProjectileHealth.cs reading UserData/FreedomArrow/projectile-health.json.
Nothing else differs. For each HP: write the identity files, build the runtime, run package_0_8_next.py. The identity files go
back to dev.12 at the end (the branch stays at dev.12 plus the hook); the per-variant receipts are kept.
Usage: missile_hp_variants.py 5 7 9
       missile_hp_variants.py 7 --burst-pause   (0.9.0-dev.12-hp7-burst: also the SPAAG burst pause below)
       missile_hp_variants.py 7 --burst-pause --lead-log   (0.9.0-dev.12-hp7-burst-lead: same, named for the full CramPrediction lead log)
       missile_hp_variants.py 7 --burst-pause --lead-log --lead-fix   (...-lead-fix: names the build with the secant lead solver)
       missile_hp_variants.py 7 9 --no-burst   (0.9.0-dev.12-hp7-noburst, -hp9-noburst)
       missile_hp_variants.py 5 7 --tier   (0.9.0-dev.12-hp5-tier, -hp7-tier: no bursts + TIER_DAMAGE)
       missile_hp_variants.py 5 --tier2   (0.9.0-dev.12-hp5-tier2: Lateralus 10:39 PST "lets try this", one hit harder per tier: 1.0/1.3/1.7)
       missile_hp_variants.py 5 --burst-tier   (0.9.0-dev.12-hp5-burst-tier: Lateralus 11:29 PST "yes build that test build for me")
       missile_hp_variants.py 5 --burst-tier3   (0.9.0-dev.12-hp5-burst-tier3: Lateralus 11:54 PST "bring back the lost DPS as
           proposed" + "the Heavy guns need a burst limit to prevent them from shooting down more than 3 SEAD missiles with the gun
           alone": middle burst 7, damage per round that restores dev.12 DPS (burst pauses in, reload out) while staying in 2.5-4.99
           (2-hit kill at 5 HP): PIVADS 4.0, ZSU-23/PGZ-04/04A/88 4.6, C-RAM 2.7, PGZ-95 2.6, 30/35 mm 4.0; heavy burst 11
           (3 kills: 3+4+4 rounds) pause 1.5-2.0 s, damage 4.9 (cap below 5.0; dev.12 DPS would need 6.7 = 1-hit kills)
       missile_hp_variants.py 5 --burst-tier --mid-burst 7   (0.9.0-dev.12-hp5-burst-tier2: Lateralus 11:41 PST "the tunguska tier doesn't
           seem to be able to shoot down 2 missiles". hp5btier-1940 log: every middle burst of 5 went 2 hits on missile 1, 1 round
           already in flight when it died, 2 rounds at missile 2 still ~1.2 s out (1 hit); burst 7 = 3 for missile 1 + 4 for missile 2)

--burst-tier (Lateralus 15 Nov 2026 11:21-11:29 PST: re-introduce bursts to set how many missiles a tier stops, a burst that refills on
downtime, card DPS with burst cooldowns but without magazine reloads for the 12 SPAAG guns only, listed by weapon ID in a config file).
All 12 rounds 2.6 damage = a 2-hit kill at 5 HP, so a short window (gun guarding a neighbour) still kills; the burst sets the count:
light burst 3 (one kill + one spare) pause 2.0-3.0 s, middle burst 5 (two kills + one spare) pause 2.0-3.0 s, heavy no bursts.
Timing model work/missile-hp-tests/burstsim/sim.py (theoretical). spaag-weapons.json drives SpaagWeapons.cs (card DPS, refill after 3 s).

--tier (Lateralus 15 Nov 2026 10:16-10:23 PST: keep no bursts; power curve light guns stop 1 missile (2 occasionally), middle 2,
heavy 3; "Give me test builds for both options, and yes make the PGZ-09 on same tier as Tunguska"). A gun lands ~4 hits per
missile (hp7-noburst log), so hits per kill are light 4, middle 3, heavy 2, damage = HP/hits +~3%: hp5 1.3/1.7/2.6, hp7 1.8/2.4/3.6.

--no-burst (Lateralus 15 Nov 2026 09:52/10:00 PST: "Can we remove the bursts all together, and lower the damage to compensate ...
keep the overall damage similar to what it was before we changed the burst at all"; values "0.5 steps" chosen by him from the
equal-damage-per-minute proposal): the same 12 guns get TimeBetweenBursts 0.2 s (= TimeBetweenShotsInBurst), so they fire a steady
5 rounds/s until the magazine is empty; carried rounds unchanged. Each round's damage is NOBURST_DAMAGE (his values).

--burst-pause (Lateralus 15 Nov 2026 09:01 PST: "Yes shorten the burst, and also add the sideways aim error log... just give me a
test build with these fixes and hp7"). In his hp7 run the gun spent its burst on missile 1 of a 2-missile salvo and sat in its
1.5-3.0 s pause while missile 2 (1.5-1.8 s behind) hit it. The 12 ground SPAAG guns whose rounds can hit SEAD missiles get
TimeBetweenBursts 0.8-1.0 s; burst length and the time between shots stay. Ship CIWS 706 and the AH-64 M230LF 40 are left alone.
"""
from pathlib import Path
import json,os,re,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3];REL=ROOT/'releases/0.6';SRC=REL/'source';FA=SRC/'UserData/FreedomArrow'
PREV='0.9.0-dev.12';BUILD=186
ZIP='/nix/store/2562wqrkss8xv8z2blaa4cvgg2yknlkq-zip-3.0/bin/zip'
PY='/home/sam/tars/work/ba-dev/replicas/codex/work/freedom-arrow/.venv/bin/python'   # has pycryptodome for the map builder
DOTNET='/nix/store/d5l0ayis8vlll18v1wp9k9cxqydv2dxk-dotnet-sdk-wrapped-8.0.421/bin/dotnet'
IDENTITY=['releases/0.6/mod.json','releases/0.6/source/UserData/FreedomArrow/channel.json','releases/0.6/source/UserData/FreedomArrow/pla-build.json',
 'releases/0.6/source/runtime-qa/Runtime.cs','releases/0.6/source/runtime-qa/FreedomArrow.Runtime.csproj']
enc=lambda d:(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def edit(p,old,new):
    s=p.read_text();assert s.count(old)==1,(p,old);p.write_text(s.replace(old,new))
base=REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod';assert base.exists(),base
BURST=[19,261,309,327,345,2009181,2009365,2009555,2009599,2010639,2010659,2010673];PAUSE=(0.2,0.2) if ('--no-burst' in sys.argv or '--tier' in sys.argv or '--tier2' in sys.argv) else (0.8,1.0)
btier='--burst-tier' in sys.argv or '--burst-tier3' in sys.argv;tier2='--tier2' in sys.argv;tier='--tier' in sys.argv or tier2;nob='--no-burst' in sys.argv or tier;burst='--burst-pause' in sys.argv or nob;lead='--lead-log' in sys.argv;fix='--lead-fix' in sys.argv;CONST=FA/'constants/weapons.json';ACONST=FA/'constants/ammunitions.json'
# ammo id: (dev.12 damage, Lateralus 10:00 PST value)
NOBURST_DAMAGE={60:(3.0,1.5),231:(3.0,1.5),2009185:(3.0,1.5),          # Pantsir/Tunguska 30 mm, PGZ-09 35 mm
    2009369:(7.8,4.0),2009603:(7.8,4.0),                                   # PGL-625, FK-2000
    62:(2.0,1.0),262:(2.0,1.5),                                            # M163 PIVADS, C-RAM
    213:(2.3,1.0),2010643:(2.3,1.0),2009559:(2.3,1.0),2010663:(2.3,1.0),   # ZSU-23, PGZ-04, PGZ-04A, PGZ-88
    2010677:(2.3,1.5)}                                                     # PGZ-95
LIGHT=[62,213,2010643,2009559,2010663];MID=[262,2010677,231,60,2009185];HEAVY=[2009369,2009603]   # PIVADS ZSU-23 PGZ-04 PGZ-04A PGZ-88 | C-RAM PGZ-95 Tunguska Pantsir PGZ-09 | PGL-625 FK-2000
TIER_DAMAGE={5:(1.3,1.7,2.6),7:(1.8,2.4,3.6)}
if '--tier2' in sys.argv:TIER_DAMAGE={5:(1.0,1.3,1.7)}   # hp5-tier killed 20/20: hits per kill 5/4/3 instead of 4/3/2
LIGHT_W=[261,309,2009555,2010639,2010659];MID_W=[345,2010673,327,19,2009181];HEAVY_W=[2009365,2009599]   # weapon ids, same order as LIGHT/MID/HEAVY ammo
tier3='--burst-tier3' in sys.argv
MIDN=7 if tier3 else int(sys.argv[sys.argv.index('--mid-burst')+1]) if '--mid-burst' in sys.argv else 5
BURST_TIER={**{i:(3,2.0,3.0) for i in LIGHT_W},**{i:(MIDN,2.0,3.0) for i in MID_W},**({i:(11,1.5,2.0) for i in HEAVY_W} if tier3 else {})}
TIER3_DAMAGE={62:4.0,213:4.6,2010643:4.6,2009559:4.6,2010663:4.6,262:2.7,2010677:2.6,231:4.0,60:4.0,2009185:4.0,2009369:4.9,2009603:4.9}   # weapon id: (shots per burst, pause min, pause max)
SPAAG=FA/'spaag-weapons.json'
def burst_tier():
    assert sorted(LIGHT_W+MID_W+HEAVY_W)==sorted(BURST)
    w=json.loads(zipfile.ZipFile(base).read('UserData/FreedomArrow/constants/weapons.json'));van={r['Id']:r for r in json.load(open('/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla/WeaponsJson.json'))};changed={}
    keys=['ShotsPerBurstMin','ShotsPerBurstMax','TimeBetweenBurstsMin','TimeBetweenBurstsMax']
    for i in BURST:
        r=w.setdefault(str(i),{});changed[i]=[r.get(k,van.get(i,{}).get(k)) for k in keys]
        n,lo,hi=BURST_TIER.get(i,(None,0.2,0.2))
        r.update(TimeBetweenBurstsMin=lo,TimeBetweenBurstsMax=hi)
        if n:r.update(ShotsPerBurstMin=n,ShotsPerBurstMax=n)
    CONST.parent.mkdir(exist_ok=True);CONST.write_text(json.dumps(w,indent=2,ensure_ascii=False)+'\n')
    SPAAG.write_text(enc({'weapons':sorted(BURST),'burstRefillIdleSeconds':3.0,
        'card_dps':'Arsenal card DPS of these weapons counts burst cooldowns but not magazine reloads (Lateralus 11:29 PST)',
        'burst_refill':'a listed gun that has not fired for burstRefillIdleSeconds and is not in a burst pause starts its next burst full',
        'source':'Lateralus 15 Nov 2026, thread 1571554273639006392'}))
    return {i:dict(zip(keys,v)) for i,v in changed.items()}
def tier_damage(hp):
    l,m,h=TIER_DAMAGE[hp];new={**{i:l for i in LIGHT},**{i:m for i in MID},**{i:h for i in HEAVY}};assert set(new)==set(NOBURST_DAMAGE)
    return {i:(NOBURST_DAMAGE[i][0],v) for i,v in new.items()}
def noburst_damage(values=None):
    values=values or NOBURST_DAMAGE
    z=zipfile.ZipFile(base);a=json.loads(z.read('UserData/FreedomArrow/constants/ammunitions.json'))
    van={r['Id']:r for r in json.load(open('/home/sam/tars/work/ba-dev/replicas/codex/work/lateralus-infantry-20261110/vanilla/AmmunitionsJson.json'))}
    for i,(old,new) in values.items():
        r=a.setdefault(str(i),{});cur=r.get('Damage',van.get(i,{}).get('Damage'));assert cur==old,(i,cur,old)
        r['Damage']=new
    ACONST.parent.mkdir(exist_ok=True);ACONST.write_text(json.dumps(a,indent=2,ensure_ascii=z.read('UserData/FreedomArrow/constants/ammunitions.json').isascii())+'\n')
def burst_pause():
    w=json.loads(zipfile.ZipFile(base).read('UserData/FreedomArrow/constants/weapons.json'));changed={}
    for i in BURST:
        r=w.setdefault(str(i),{});changed[i]=[r.get('TimeBetweenBurstsMin'),r.get('TimeBetweenBurstsMax')]
        assert changed[i][0] is None or changed[i][0]>=1.5,(i,changed[i])
        r.update(TimeBetweenBurstsMin=PAUSE[0],TimeBetweenBurstsMax=PAUSE[1])
    CONST.parent.mkdir(exist_ok=True);CONST.write_text(json.dumps(w,indent=2,ensure_ascii=False)+'\n');return changed
try:
    for hp in [int(x) for j,x in enumerate(sys.argv[1:],1) if x.isdigit() and sys.argv[j-1]!='--mid-burst']:   # 11:45: '--mid-burst 7' had also built an unwanted hp7
        V=f'{PREV}-hp{hp}'+('-burst-tier'+('3' if tier3 else '' if MIDN==5 else '2') if btier else '-tier2' if tier2 else '-tier' if tier else '-noburst' if nob else ('-burst' if burst else '')+('-lead' if lead else '')+('-fix' if fix else ''))
        before=burst_tier() if btier else burst_pause() if burst else None
        dmg={i:(v[0],TIER3_DAMAGE[i] if tier3 else 2.6) for i,v in NOBURST_DAMAGE.items()} if btier else tier_damage(hp) if tier else NOBURST_DAMAGE
        if nob or btier:noburst_damage(dmg)
        (FA/'projectile-health.json').write_text(enc({'health':float(hp),'vanilla':1.0,'scope':'every CanBeTargeted projectile (MakeShellTargetable)',
            'source':'Lateralus 15 Nov 2026, thread 1571554273639006392'}))
        m=json.loads((REL/'mod.json').read_text());assert m['version']==PREV
        m['version']=V;m['description']=re.sub(r'^(Freedom Arrow 0\.9: China \(PLA\) on the full 0\.7\.0-dev\.58 game\. )',
            rf'\g<1>{V}: TEST BUILD, dev.12 with every interceptable missile at {hp} HP (vanilla 1)'+((', 12 SPAAG guns 2.6-4.9 damage per round (dev.12 DPS), light guns burst 3 and middle guns burst 7 with a 2-3 s pause, heavy guns burst 11 with a 1.5-2 s pause,' if tier3 else ', 12 SPAAG guns 2.6 damage per round, light guns burst 3 and middle guns burst %d with a 2-3 s pause'%MIDN+', heavy guns no bursts,')+' bursts refill after 3 s without firing, card DPS without magazine reload' if btier else '')+(((', 12 SPAAG guns fire steadily (no bursts), tiered damage %s light/middle/heavy, missile motion recorded from launch'%('/'.join(map(str,TIER_DAMAGE[hp]))) if tier else ', 12 SPAAG guns fire steadily (no bursts) with lower damage per round, missile motion recorded from launch') if nob else ', SPAAG burst pause 0.8-1.0 s, turret aim error in the AA log') if burst else '')+(', full gun lead-correction log' if lead else '')+(', lead correction solves head-on missiles (secant)' if fix else '')+'; ',m['description']);assert V in m['description']
        (REL/'mod.json').write_text(enc(m))
        c=json.loads((FA/'channel.json').read_text());c['package_version']=V;(FA/'channel.json').write_text(enc(c))
        b=json.loads((FA/'pla-build.json').read_text());b.update(build=BUILD,label='Freedom Arrow '+V);(FA/'pla-build.json').write_text(enc(b))
        edit(SRC/'runtime-qa/Runtime.cs','"Freedom Arrow", "0.9.0-dev.12"',f'"Freedom Arrow", "{V}"')
        edit(SRC/'runtime-qa/FreedomArrow.Runtime.csproj','<Version>0.9.0-dev.12</Version>',f'<Version>{V}</Version>')
        (FA/f'pla-{V}.json').write_text(enc({'version':V,'base':PREV,'build':BUILD,'projectile_health':float(hp),'vanilla_health':1.0,
            'hook':'ProjectileSpawnerHelper.MakeShellTargetable postfix (RVA 0x7DF1E0) writes _health, MaxHealth, HalfHealth',
            'data_changes':{'weapons':before,'ammunition_damage':{str(i):list(v) for i,v in dmg.items()},'spaag_weapons':json.loads(SPAAG.read_text())} if btier else ({'weapons':{str(i):{'TimeBetweenBursts_patch_before':before[i],'after':list(PAUSE)} for i in BURST}}|({'ammunition_damage':{str(i):list(v) for i,v in dmg.items()}} if nob else {})) if burst else 'none','verified':'build checks only; not yet seen in a game'}))
        subprocess.run([DOTNET,'build','-c','Release','-p:GameDir=/home/sam/tars/work/ba-dev/game'],cwd=SRC/'runtime-qa',check=True,
            env={**os.environ,'DOTNET_CLI_TELEMETRY_OPTOUT':'1'})
        subprocess.run([PY,str(ROOT/'tools/pla-specs/package_0_8_next.py'),'--prev',PREV,'--version',V,'--build',str(BUILD),
            '--base',str(base),'--outdir',str(REL/'out/0.8'),'--zip',ZIP],check=True,env={**os.environ,'BA_DEVPOST_SKIP':'Lateralus missile HP test build, not a dev build'})
        subprocess.run(['git','checkout','--',*IDENTITY],cwd=ROOT,check=True)
finally:
    subprocess.run(['git','checkout','--',*IDENTITY],cwd=ROOT,check=True);(FA/'projectile-health.json').unlink(missing_ok=True);CONST.unlink(missing_ok=True);ACONST.unlink(missing_ok=True);SPAAG.unlink(missing_ok=True)
