"""Mount weapon slots: a mount may carry at most as many weapons as the most any vanilla mount with the same model carries
(model-less mounts: the most on any vanilla model-less mount of the same body), and no weapon twice, unless it is a vanilla mount
as shipped; and a deployable unit's loadout may only use slot numbers that vanilla uses on the same body (vanilla loadout
slots, or its default mounts). More weapons than the model has slots throws IndexOutOfRange in UnitBuilder.SetupWeaponComponents at spawn
("CombatSystem initialization ... failed") and the match freezes (J-20 14 Nov 2026; FK-2000 13 Nov).
A child turret's weapon orders must be 0..n-1 (all 86 vanilla child turrets are): the game puts each weapon at index Order, so a gap
leaves a null in the list and Turrets.CloneWithClonedWeaponsAndTurrets throws (unit card, editor; ZTZ-99A LSDW Order 2, dev.23 16 Nov).
Usage: check_mount_weapons.py PACKAGE.bamod VANILLA_DIR   (exit 1 and list the mounts when any are over)"""
import json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'mod')]
from pipeline.tables import FIELD_TO_FILE
TABS=('Units','TurretsJson','TurretUnitsJson','TurretWeaponsJson','WeaponsJson','OptionsJson','ModificationsJson','SpecializationAvailabilitiesJson')
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
# F-35A/B/C "Wingtips F35 2xAIM9" (0.6 dev.52 test slot, 8 Nov): slots 5-6, past vanilla F-35 slots 0-4. Never confirmed in a
# game; held for Osama's call (14 Nov) rather than silently passed.
# dev.33 (Osama 16 Nov 16:0x): their "Empty" counterparts 20161/20163/20165 now put the vanilla blank mount 160 on the same slots 5-6,
# so swapping back to Empty removes the Sidewinders (vanilla Empty options do the same, e.g. AH-1Z, Ka-52). Same slots, same exception.
KNOWN={20162,20164,20166,20161,20163,20165}
def slots(t,v):
    def opts(tt):
        m={}
        for o in tt['OptionsJson'].values():
            md=tt['ModificationsJson'].get(o.get('ModificationId'))
            if md and md['UnitId'] in tt['Units']:m.setdefault(md['UnitId'],[]).append(o)
        return m
    vo,to,vu=opts(v),opts(t),users(v);used,dflt={},{}
    for u,r in v['Units'].items():
        b=r['ModelFileName'];used.setdefault(b,set());dflt.setdefault(b,{0})
        used[b]|={i for o in vo.get(u,[]) for i in range(21) if o.get(f'Turret{i}Id')}
        dflt[b]|=set(range(sum(1 for k,us in vu.items() if u in us and v['TurretsJson'].get(k,{}).get('IsDefault'))))
    ok={b:used[b] or dflt[b] for b in used}   # vanilla loadout slots; bodies with none (2S43 Malva) allow their default mounts
    deploy={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values()}
    deploy|={o['ReplaceUnitId'] for u in deploy for o in to.get(u,[]) if o.get('ReplaceUnitId')}
    bad=[]
    for u in sorted(deploy):
        if u not in t['Units'] or u in v['Units'] and to.get(u)==vo.get(u):continue
        b=t['Units'][u]['ModelFileName']
        if b not in ok:continue
        for o in to.get(u,[]):
            extra=sorted(i for i in range(21) if o.get(f'Turret{i}Id') and i not in ok[b])
            if extra and o['Id'] not in KNOWN:bad.append((t['Units'][u]['HUDName'],u,o['Id'],o.get('Name'),b,extra,sorted(ok[b])))
    return bad
def holes(t):
    o={}
    for r in t['TurretWeaponsJson'].values():o.setdefault(r['TurretId'],[]).append(r['Order'])
    # child turrets: orders 0..n-1 (dev.23 LSDW crash); every turret: no Order above its weapon count (0.9.4.1: card NRE in
    # RefundSystem.GetAmmoResupplyTime from the ZTZ 12.7 mm mount at [2] with one weapon; LoadWeapons pads Order - rows empty slots)
    return sorted((k,t['TurretsJson'].get(k,{}).get('Name'),sorted(v)) for k,v in o.items() if (t['TurretsJson'].get(k,{}).get('ParentTurretId') and sorted(v)!=list(range(len(v)))) or max(v)>len(v))
if __name__=='__main__':
    van=Path(sys.argv[2]);t,v=tables(van,zipfile.ZipFile(sys.argv[1])),tables(van);bad=over(t,v);bs=slots(t,v);hs=holes(t)
    for k,n,mf,c,lim,us in bad:print(f'{k} {n}: {c} weapons on model {mf} (vanilla most {lim}); units {", ".join(us)}')
    for h,u,o,n,b,x,okk in bs:print(f'{h} ({u}) loadout {o} {n}: slots {x} on body {b} (vanilla uses {okk})')
    for k,n,o in hs:print(f'{k} {n}: child turret weapon orders {o}, not 0..{len(o)-1}')
    print('mounts over their weapon slots',len(bad),'| loadout slots the body never uses',len(bs),'| child turrets with an order gap',len(hs));sys.exit(1 if bad or bs or hs else 0)
