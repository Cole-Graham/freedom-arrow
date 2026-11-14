"""Loadout swap prices: a loadout option that swaps the card to another unit row (ReplaceUnitId) must leave that row's Cost at
base Cost + option Cost, as in vanilla (80 swaps, 0 exceptions). The deck editor shows base + option; the battlegroup overview in
the Arsenal shows the swap row's own Cost (12the12, #bug-report 14 Nov 2026: Spetsnaz Alpha stand-off 95 vs 90).
Usage: audit_swap_prices.py PACKAGE.bamod VANILLA_DIR   (exit 1 and list the rows when any differ)"""
import json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'releases/0.6')]
from pipeline.tables import FIELD_TO_FILE
def mismatches(U,O,M):
    bad=[]
    for o in O.values():
        r=o.get('ReplaceUnitId') or 0;m=M.get(o['ModificationId'])
        if not r or not m or m['UnitId'] not in U or r==m['UnitId']:continue
        b=m['UnitId'];assert r in U,(o['Id'],'swaps to missing unit',r)
        if U[r]['Cost']!=U[b]['Cost']+o['Cost']:bad.append((b,U[b].get('HUDName'),U[b]['Cost'],o['Id'],o['Cost'],r,U[r]['Cost']))
    return bad
if __name__=='__main__':
    van=Path(sys.argv[2]);z=zipfile.ZipFile(sys.argv[1]);t={}
    for tab in ('Units','OptionsJson','ModificationsJson'):
        t[tab]={r['Id']:r for r in json.loads((van/(tab+'.json')).read_text())}
        for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[tab])).items():
            if v is None:t[tab].pop(int(k),None)
            else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    bad=mismatches(t['Units'],t['OptionsJson'],t['ModificationsJson'])
    for b,n,bc,o,oc,r,rc in bad:print(f'{n} ({b}): {bc} + option {o} {oc:+} = {bc+oc}, but swap row {r} costs {rc}')
    print('swap price mismatches',len(bad));sys.exit(1 if bad else 0)
