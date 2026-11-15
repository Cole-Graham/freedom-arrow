"""Body slot weapons: a mount at slot (Order) k may carry at most as many weapons as any vanilla unit with the same body
(Units.ModelFileName) carries at slot k, when vanilla uses that slot. More throws IndexOutOfRange in UnitBuilder.SetupWeaponComponents
at spawn ("CombatSystem initialization ... failed") and the match stalls: QN-506 on 14 Nov 2026 (BMPT body slot 2: vanilla 1 AG-17,
QN-506 had 2 missiles). check_mount_weapons.py compares by turret model, which missed it.
Usage: check_slot_weapons.py PACKAGE.bamod VANILLA_DIR   (exit 1 and list the mounts when any are over)"""
import json,sys,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'releases/0.6')]
from pipeline.tables import FIELD_TO_FILE
TABS=('Units','TurretUnitsJson','TurretWeaponsJson')
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
    sys.exit(1 if bad else 0)
main()
