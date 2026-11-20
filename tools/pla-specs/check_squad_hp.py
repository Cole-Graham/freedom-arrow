"""Infantry squad health = 5 HP per soldier, as in every vanilla squad that the game ships (4 men 20, 12 men 60; the Armor row's
MaxHealthPoints). Osama 19 Nov 2026 (thread 1567745029781454889, QQ bug FA-003 "Godswords should have 60 HP, not 30"): six China squads
were off (Godswords 12 men / 30, five 4-man teams 25 or 30); fixed in 0.9.2-dev.1. Checks every infantry unit (Units.Type 2) that a
specialization offers, on every UnitArmors row it has.
Usage: check_squad_hp.py PACKAGE.bamod VANILLA_DIR  |  check_squad_hp.py --constants DIR VANILLA_DIR   (exit 1 and list the squads that are off)"""
import json,sys,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'releases/0.6')]
from pipeline.tables import FIELD_TO_FILE
TABS=('Units','ArmorsJson','UnitArmorsJson','SquadMembersJson','SpecializationAvailabilitiesJson')
def tables(van,read):
    t={}
    for tab in TABS:
        t[tab]={r['Id']:r for r in json.loads((van/(tab+'.json')).read_text())}
        for k,v in json.loads(read(FIELD_TO_FILE[tab])).items():
            if v is None:t[tab].pop(int(k),None)
            else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    return t
def off(t):
    men=Counter(r['UnitId'] for r in t['SquadMembersJson'].values());live={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values()}
    bad=[]
    for r in t['UnitArmorsJson'].values():
        u=t['Units'].get(r['UnitId'])
        if not u or u.get('Type')!=2 or u['Id'] not in live or not men[u['Id']]:continue
        hp=t['ArmorsJson'].get(r['ArmorId'],{}).get('MaxHealthPoints')
        if hp!=5*men[u['Id']]:bad.append((u['Id'],u.get('HUDName'),men[u['Id']],hp,r['ArmorId']))
    return bad
def main():
    a=sys.argv[1:]
    if a[0]=='--constants':d=Path(a[1]);read=lambda fn:(d/fn).read_text();van=Path(a[2])
    else:z=zipfile.ZipFile(a[0]);read=lambda fn:z.read('UserData/FreedomArrow/constants/'+fn);van=Path(a[1])
    bad=off(tables(van,read))
    for b in bad:print('squad HP is not 5 per soldier: unit %s %s, %s men, HP %s (armour row %s)'%b)
    print('check_squad_hp:',len(bad),'squads off');sys.exit(1 if bad else 0)
if __name__=='__main__':main()
