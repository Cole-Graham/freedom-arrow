"""Freedom Arrow 0.9.1-dev.1 data over exact 0.9.0-dev.44 (19 Nov 2026). Was the 0.9.0-dev.45 batch; Lateralus 19 Nov 06:2x PST: "create a 0.9.1
development branch and move the latest dev build along with any queued changes into a 0.9.1-dev.1 build". Opened by BA Codex thread 1572962048705429598 (Lateralus, JRVG-1 overpressure).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.1-dev.1';PREV='0.9.0-dev.44'
# dev.44 was built in out/local-dev44.
BASE=json.loads((REL/f'out/local-dev44/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-dev44/FreedomArrow-{PREV}-complete.bamod'
with base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(base);t={};patches={};native={}
for tab,fn in FIELD_TO_FILE.items():
    t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};native[tab]=set(t[tab]);patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
    for k,v in patches[tab].items():
        if v is None:t[tab].pop(int(k),None)
        else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
g=Graph(t,patches,native);U=t['Units'];checks=0;rec={}
def ok(c,l):
    global checks
    assert c,l;checks+=1
_A=t['AmmunitionsJson'];_WA=t['WeaponAmmunitionsJson']
# ---------- JRVG-1 HE: no overpressure (Lateralus 19 Nov 2026 05:1x PST, thread 1572962048705429598: "JRVG-1 seems to be attacking the top armor of tanks
# via the overpressure mechanic by firing HE at it" ... "yes"). Ammo 2009953 '76 mm HE (proximity)' (JRVG-1 952 only) got OverpressureRadius 4.5 in Build 68
# (apply_build68.py copied the Mark 45 127 mm HE, ammo 446, an indirect ground-only shell). The round kept direct fire and TargetType 63 (Vehicle bit).
# ShellHitSystem.InternalUpdate sets IsTargetOverpressured on the directly struck unit when OverpressureRadius > 0, with no distance test (1.2.2.1 RVA
# 0x7fe0f0), so every direct HE hit used roof armour: 8 x 60^2/(60^2+100^2) = 2.12 per hit on an MBT roof (HEAT top 100), ~7 hits per 14 HP tank.
# No vanilla AA gun round has OverpressureRadius > 0 (Derivatsiya 57 mm HE 201 = 0). After: side HEAT 200 = 0.66, front ~0.02-0.03.
ok(U[952]['HUDName']=='JRVG-1' and _A[2009953]['HUDName']=='76 mm HE (proximity)' and _A[2009953]['OverpressureRadius']==4.5,'JRVG-1 proximity HE, OP 4.5')
ok({r['UnitId'] for r in _WA.values() if r['AmmunitionId']==2009953}=={952},'ammo 2009953 used by JRVG-1 only')
ok(_A[201]['Name']=='Round 57 2A91 Derivatsiya AAG HE T3' and _A[201]['OverpressureRadius']==0,'vanilla Derivatsiya HE has no overpressure')
g.put('AmmunitionsJson',2009953,{'OverpressureRadius':0.0})
ok(_A[2009953]['OverpressureRadius']==0.0,'JRVG-1 proximity HE OP 0')
rec['jrvg1_he_no_overpressure']={'ammo':2009953,'unit':952,'OverpressureRadius':[4.5,0.0],'why':'direct hits with OP > 0 always use roof armour','verified':'data checks only; not seen in game'}
# ---------- Air-to-air motors match their ranges; R-37 accuracy back to 1.0 (Lateralus 19 Nov 2026 06:1x PST, thread 1572962048705429598: "Ok fix the
# AMRAAM-motor missiles and B-21 JATMs. Also ... remove the 0.9 accuracy from the R-37 and set it back to 1.0"). docs/engine/missile-flight.md: a missile
# burns BurnTime, coasts at -0.13 x MaxSpeed/s and dies at 0.3 x MaxSpeed; the table range only gates firing. 0.6 dev.52 and PLA Build55 raised ranges
# without motors. Launched at 225 against a target fleeing at 225 (calculated): the AMRAAM motor (MaxSpeed 1150, Acceleration 200, BurnTime 4) catches out
# to 3694, below its 4000/4500 ranges. BurnTime 4.5 reaches MaxSpeed and catches to 4688. The B-21 JATM 2001658 (5500) takes the motor of the F-22
# AIM-260 531 (Acceleration 300, BurnTime 5): 6013. PL-12 2011537 (3500) already catches and stays. R-37 312/921 DispersionHorizontalRadius 0.9 -> 1.0.
_U=t['Units']
def _air_only(i):return all(_U[r['UnitId']]['Type']==16 for r in _WA.values() if r['AmmunitionId']==i) and any(r['AmmunitionId']==i for r in _WA.values())
_AMR=[89,159,920,2016380,2016390,2011459,2011471,2016398,2017953]
for _i in _AMR+[2001658,2011537]:
    _r=_A[_i];ok((_r['MaxSpeed'],_r['Acceleration'],_r['BurnTime'],_r['MainEngineIgnitionDelay'])==(1150.0,200.0,4.0,0.5) and _r['TargetType']&16 and _air_only(_i),(_i,_r['HUDName'],'AMRAAM motor, aircraft only'))
for _i in _AMR:
    ok(_A[_i]['HighAltRange'] in (4000.0,4500.0),(_i,'range 4000/4500'));g.put('AmmunitionsJson',_i,{'BurnTime':4.5})
ok(_A[2011537]['HighAltRange']==3500.0,'J-8 PL-12 range 3500, left as is')
ok(_A[531]['HUDName']=='AIM-260' and (_A[531]['MaxSpeed'],_A[531]['Acceleration'],_A[531]['BurnTime'])==(1150.0,300.0,5.0),'F-22 AIM-260 motor')
ok(_A[2001658]['HUDName']=='AIM-260 JATM' and _A[2001658]['HighAltRange']==5500.0,'B-21 JATM 5500')
g.put('AmmunitionsJson',2001658,{'Acceleration':_A[531]['Acceleration'],'BurnTime':_A[531]['BurnTime']})
for _i in (312,921):
    ok(_A[_i]['HUDName']=='R-37' and _A[_i]['DispersionHorizontalRadius']==0.9,(_i,'R-37 accuracy 0.9 (dev.52)'));g.put('AmmunitionsJson',_i,{'DispersionHorizontalRadius':1.0})
ok(all(_A[_i]['BurnTime']==4.5 for _i in _AMR) and (_A[2001658]['Acceleration'],_A[2001658]['BurnTime'])==(300.0,5.0) and _A[312]['DispersionHorizontalRadius']==_A[921]['DispersionHorizontalRadius']==1.0,'air-to-air motor and R-37 accuracy set')
rec['aam_motor_match_range']={'burn_4_to_4_5':_AMR,'b21_jatm_2001658':{'Acceleration':[200.0,300.0],'BurnTime':[4.0,5.0]},'unchanged':{'2011537':'PL-12, range 3500, catches at 3694'},
    'r37_accuracy':{'312':[0.9,1.0],'921':[0.9,1.0]},'catch_at_225':{'amraam_before':3694,'amraam_after':4688,'jatm_after':6013},'verified':'data checks only; calculated, not seen in game'}
# ---------- Nukes cost about a third more (Lateralus 19 Nov 2026 06:2x PST, thread 1572724406642286692: "we need to increase the price of all nukes.
# e.g. MiG-31K (S) should go from 1500 -> 2000, B-2 Spirit with B61 Nuke should go from 1400 -> 1850, DF-31A Nuclear should go from 1000 -> 1350. Use your
# best judgement for any others I missed"). Every purchasable nuke (B61, Kh-102, Kh-47M2 nuke, DF-31A warhead; the LRSO/ALCM nuke rows and the F-117/B-52H
# B61 rows have no option): the same steps, 1000 -> 1350 for B-1B and Tu-160. Plane nukes are loadout options, so the option price moves (total = base + option).
_O=t['OptionsJson'];_M=t['ModificationsJson']
_NUKE_UNITS={702:('MiG-31K (S)',1500,2000),1032:('DF-31A Nuclear',1000,1350)}
_NUKE_OPTS={1083:(299,'B-2 Spirit',1200,1650),20177:(965,'B-21 Raider',1200,1650),1026:(293,'B-1B Lancer',800,1150),1740:(317,'Tu-160',800,1150)}
_nk={}
for _u,(_n,_old,_new) in _NUKE_UNITS.items():
    ok(U[_u]['HUDName'].strip()==_n and U[_u]['Cost']==_old,(_u,_n,_old));g.put('Units',_u,{'Cost':_new});_nk[_n]=[_old,_new]
for _o,(_u,_n,_old,_new) in _NUKE_OPTS.items():
    ok(_M[_O[_o]['ModificationId']]['UnitId']==_u and U[_u]['HUDName'].strip()==_n and _O[_o]['Cost']==_old and U[_u]['Cost']==200,(_o,_n,'nuke option',_old))
    g.put('OptionsJson',_o,{'Cost':_new});_nk[_n]=[200+_old,200+_new]
ok(_nk=={'MiG-31K (S)':[1500,2000],'DF-31A Nuclear':[1000,1350],'B-2 Spirit':[1400,1850],'B-21 Raider':[1400,1850],'B-1B Lancer':[1000,1350],'Tu-160':[1000,1350]},'nuke totals')
rec['nuke_prices']={'totals':_nk,'units':list(_NUKE_UNITS),'options':list(_NUKE_OPTS)}
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
