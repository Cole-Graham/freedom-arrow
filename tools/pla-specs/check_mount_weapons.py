"""Mount weapon slots: a mount may carry at most as many weapons as the most any vanilla mount with the same model carries
(model-less mounts: the most on any vanilla model-less mount of the same body), and no weapon twice, unless it is a vanilla mount
as shipped. More weapons than the model has slots throws IndexOutOfRange in UnitBuilder.SetupWeaponComponents at spawn
("CombatSystem initialization ... failed") and the match freezes (J-20 14 Nov 2026; FK-2000 13 Nov).
Usage: check_mount_weapons.py PACKAGE.bamod VANILLA_DIR   (exit 1 and list the mounts when any are over)"""
import json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'releases/0.6')]
from pipeline.tables import FIELD_TO_FILE
TABS=('Units','TurretsJson','TurretUnitsJson','TurretWeaponsJson','WeaponsJson')
def tables(van,z=None):
    t={}
    for tab in TABS:
        t[tab]={r['Id']:r for r in json.loads((van/(tab+'.json')).read_text())}
        if z:
            for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[tab])).items():
                if v is None:t[tab].pop(int(k),None)
                else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    return t
def weapons(t):
    m={}
    for r in sorted(t['TurretWeaponsJson'].values(),key=lambda r:(r['Order'],r['Id'])):m.setdefault(r['TurretId'],[]).append(r['WeaponId'])
    return m
def users(t):
    u={}
    for r in t['TurretUnitsJson'].values():
        if r['UnitId'] in t['Units']:u.setdefault(r['TurretId'],set()).add(r['UnitId'])
    return u
def over(t,v):
    vw,vu,tw,tu=weapons(v),users(v),weapons(t),users(t);cap,body={},{}
    for k,ws in vw.items():
        mf=v['TurretsJson'].get(k,{}).get('ModelFileName')
        if mf:cap[mf]=max(cap.get(mf,0),len(ws))
        elif k in v['TurretsJson']:
            for u in vu.get(k,()):b=v['Units'][u]['ModelFileName'];body[b]=max(body.get(b,0),len(ws))
    bad=[]
    for k,ws in tw.items():
        if k not in t['TurretsJson'] or k not in tu or ws==vw.get(k):continue
        mf=t['TurretsJson'][k].get('ModelFileName')
        lim=cap.get(mf) if mf else min(body.get(t['Units'][u]['ModelFileName'],99) for u in tu[k])
        if lim and len(ws)>lim or len(set(ws))<len(ws):
            bad.append((k,t['TurretsJson'][k]['Name'],mf,len(ws),lim,sorted({t['Units'][u]['HUDName'] for u in tu[k]})))
    return bad
if __name__=='__main__':
    van=Path(sys.argv[2]);bad=over(tables(van,zipfile.ZipFile(sys.argv[1])),tables(van))
    for k,n,mf,c,lim,us in bad:print(f'{k} {n}: {c} weapons on model {mf} (vanilla most {lim}); units {", ".join(us)}')
    print('mounts over their weapon slots',len(bad));sys.exit(1 if bad else 0)
