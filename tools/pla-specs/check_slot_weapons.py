"""Body slot weapons: a mount at slot (Order) k may carry at most as many weapons as any vanilla unit with the same body
(Units.ModelFileName) carries at slot k, when vanilla uses that slot. More throws IndexOutOfRange in UnitBuilder.SetupWeaponComponents
at spawn ("CombatSystem initialization ... failed") and the match stalls: QN-506 on 14 Nov 2026 (BMPT body slot 2: vanilla 1 AG-17,
QN-506 had 2 missiles). check_mount_weapons.py compares by turret model, which missed it.
Second rule (19 Nov 2026, 1.2.2.1 code): the unit's turret i takes the BODY prefab's turret script MainTurrets[i] (InitCombatSystem 0x3470C0) and
SetupWeaponComponents reads that script's weapon point k for the weapon at padded list index k (rows padded with nulls up to their Order;
bounds check 0x351EEE). On a body slot that vanilla fills only with model-less hull mounts, a weapon's padded index must stay below the most
weapons vanilla puts there. The count rule alone let QN-506 keep failing after 0.9.0-dev.7 (Order 2 on the BMPT's 1-point slot 2; also
Type 86 / ZBD-86, ZBD-05, FK-2000; fixed in 0.9.2-dev.1).
Usage: check_slot_weapons.py PACKAGE.bamod VANILLA_DIR   (exit 1 and list the mounts when any are over)"""
import json,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'releases/0.6')]
from pipeline.tables import FIELD_TO_FILE
TABS=('Units','TurretsJson','TurretUnitsJson','TurretWeaponsJson')
def tables(van,z=None):
    t={}
    for tab in TABS:
        t[tab]={r['Id']:r for r in json.loads((van/(tab+'.json')).read_text())}
        if z:
            for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[tab])).items():
                if v is None:t[tab].pop(int(k),None)
                else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    return t
def count(t):
    n=defaultdict(int)
    for w in t['TurretWeaponsJson'].values():n[w['TurretId']]+=1
    return n
def main():
    van=tables(Path(sys.argv[2]));t=tables(Path(sys.argv[2]),zipfile.ZipFile(sys.argv[1]));nv,nt=count(van),count(t);cap=defaultdict(int)
    for tu in van['TurretUnitsJson'].values():
        u=van['Units'].get(tu['UnitId'])
        if u:k=(u.get('ModelFileName'),tu['Order']);cap[k]=max(cap[k],nv[tu['TurretId']])
    bad=[]
    for tu in t['TurretUnitsJson'].values():
        u=t['Units'].get(tu['UnitId'])
        if not u or tu['Id'] in van['TurretUnitsJson'] and van['TurretUnitsJson'][tu['Id']]==tu:continue
        k=(u.get('ModelFileName'),tu['Order'])
        if cap.get(k,0)>0 and nt[tu['TurretId']]>cap[k]:bad.append((u['Id'],u.get('HUDName'),k[0],tu['Order'],nt[tu['TurretId']],cap[k]))
    print('mounts over their body slot',len(bad));[print(' unit %s %s body %s slot %s: %s weapons, vanilla max %s'%b) for b in sorted(bad)]
    hull=hull_index(t,van);print('weapons past the body hull slot points',len(hull))
    [print(' unit %s %s body %s slot %s turret %s: weapon %s at index %s, vanilla points %s'%h) for h in sorted(hull)]
    sys.exit(1 if bad or hull else 0)
def padded(t,tid):
    L=[]
    for r in sorted((r for r in t['TurretWeaponsJson'].values() if r['TurretId']==tid),key=lambda r:(r['Order'],r['Id'])):
        L+=[None]*max(0,r['Order']-len(L));L.append(r['WeaponId'])
    return L
def hull_index(t,van):
    kinds=defaultdict(set);pts=defaultdict(int)
    for tu in van['TurretUnitsJson'].values():
        u=van['Units'].get(tu['UnitId']);tr=van['TurretsJson'].get(tu['TurretId'])
        if not u or not tr or tr.get('ParentTurretId'):continue
        k=(u.get('ModelFileName'),tu['Order']);kinds[k].add(bool(tr.get('ModelFileName')))
        if not tr.get('ModelFileName'):pts[k]=max(pts[k],len(padded(van,tu['TurretId'])))
    bad=[]
    for tu in t['TurretUnitsJson'].values():
        u=t['Units'].get(tu['UnitId']);tr=t['TurretsJson'].get(tu['TurretId'])
        if not u or not tr or tr.get('ParentTurretId'):continue
        if tu['Id'] in van['TurretUnitsJson'] and van['TurretUnitsJson'][tu['Id']]==tu and tu['TurretId'] in van['TurretsJson']:continue
        k=(u.get('ModelFileName'),tu['Order'])
        if kinds.get(k)!={False} or not pts[k]:continue
        for i,w in enumerate(padded(t,tu['TurretId'])):
            if w is not None and i>=pts[k]:bad.append((u['Id'],u.get('HUDName'),k[0],tu['Order'],tu['TurretId'],w,i,pts[k]))
    return bad
if __name__=='__main__':main()
