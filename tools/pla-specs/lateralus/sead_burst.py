"""SEAD missiles fire in bursts of 2 (Lateralus 16 Nov 2026, thread 1571554273639006392, proposal A, "Implement proposal A for SEAD";
helicopter SEAD missiles too, and a 2-missile plane may fire both within 1 s: "Yes to both").

Goal: bursts of 2, about 1 s between the two shots, 1.5-2 s between bursts, as equal as data allows for 2, 4 and 6 missiles.
Read from GameAssembly (UnitBuilder.CombineWeapons RVA 0x3434F0 -> CombinePylonsOnAircraft 0x341330, unit types 16 plane and 8 helicopter):
identical pylons are merged into one launcher. Its magazine is the sum, aim time is averaged, and for guided rounds the pause between
bursts is averaged and divided by the merged count. ShotsPerBurst and TimeBetweenShotsInBurst are copied unchanged from the pylon.
Measured (Lateralus 15 Nov hp5 tier tests, 407 launches): MiG-29K 4x Kh-31P = one launcher, magazine 4, pause 1.503-2.000 s = 6-8 s / 4.

So only ShotsPerBurst (1 -> 2) and TimeBetweenShotsInBurst (0 -> 1.0 s, data has one value, no range) change; TimeBetweenBursts stays 6-8 s
(planes) so 4 missiles give 2+2 with 1.5-2 s between bursts, 2 missiles one burst, 6 (H-6K) 2+2+2 with about 1.0-1.33 s. Not seen in a game.

Use: apply(t, put, ok) from a dev apply file (t = merged tables, put(table, id, fields) writes a patch, ok(cond, label) is a check),
or `python sead_burst.py --vanilla DIR --package FILE.bamod` to run the checks against a package (writes nothing).
"""
import argparse,json,sys,zipfile
from pathlib import Path
SEAD_WEAPONS=[267,358,395,407,449,542,2016699,2016727,2017632,2017962,2018029,2018455,2019306]   # every weapon that carries Seeker 200 ammo
OLD={'ShotsPerBurstMin':1,'ShotsPerBurstMax':1,'TimeBetweenShotsInBurst':0.0}
NEW={'ShotsPerBurstMin':2,'ShotsPerBurstMax':2,'TimeBetweenShotsInBurst':1.0}
def apply(t,put,ok):
    A=t['AmmunitionsJson'];W=t['WeaponsJson'];WA=t['WeaponAmmunitionsJson'];U=t['Units']
    sead={i for i,a in A.items() if a.get('Seeker')==200}
    found=sorted({r['WeaponId'] for r in WA.values() if r.get('AmmunitionId') in sead and r.get('UnitId') in U})
    ok(found==SEAD_WEAPONS,f'SEAD weapons are exactly the expected 13: {found}')
    for w in SEAD_WEAPONS:
        ok(all(r.get('AmmunitionId') in sead for r in WA.values() if r.get('WeaponId')==w),f'weapon {w} only carries SEAD ammo')
        ok(all(W[w].get(k)==v for k,v in OLD.items()),f'weapon {w} {W[w].get("Name")} still single shot: {[W[w].get(k) for k in OLD]}')
        ok(W[w].get('CanBeMerged') is True,f'weapon {w} merges on aircraft')
        put('WeaponsJson',w,dict(NEW))
        ok(all(W[w].get(k)==v for k,v in NEW.items()),f'weapon {w} now bursts of 2')
    return {'weapons':SEAD_WEAPONS,'before':OLD,'after':NEW,'timeBetweenBursts':'unchanged (6-8 s planes, 2-5 s helicopters)'}
if __name__=='__main__':
    ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT)]
    from pipeline.tables import FIELD_TO_FILE
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--package',type=Path,required=True);a=p.parse_args()
    z=zipfile.ZipFile(a.package);t={};patches={};n=[0]
    for tab,fn in FIELD_TO_FILE.items():
        t[tab]={r['Id']:r for r in json.loads((a.vanilla/(tab+'.json')).read_text())};patches[tab]=json.loads(z.read('UserData/FreedomArrow/constants/'+fn))
        for k,v in patches[tab].items():
            if v is None:t[tab].pop(int(k),None)
            else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    def put(tab,i,f):t[tab][i].update(f);patches[tab].setdefault(str(i),{}).update(f)
    def ok(c,l):
        assert c,l;n[0]+=1
    rec=apply(t,put,ok);print(json.dumps({'checks':n[0],**rec,'patch':{str(w):patches['WeaponsJson'][str(w)] for w in SEAD_WEAPONS}},indent=1))
