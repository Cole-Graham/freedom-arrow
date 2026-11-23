"""China infantry armour floor (Osama 19 Nov 2026: "make sure Chinese infantry armor matches other factions"). Vanilla gives line squads
ArmorValue 6, airborne/marine line infantry and their recon and weapon teams 8, SF and engineers 10. Each pinned China card must have at least
the ArmorValue of its vanilla counterpart. Add new airborne/marine/engineer/SF cards here when they are made.
Usage: check_infantry_armor.py PACKAGE.bamod VANILLA_DIR   (exit 1 and list the cards when any are below)"""
import json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'mod')]
from pipeline.tables import FIELD_TO_FILE
FLOOR={1136:8,1192:8,1224:8,1142:8,1194:8,1193:8,1199:8,1146:8,1176:8,   # Airborne, Marines, Marine Recon, Pathfinders, Marine teams, Weapons Squad, Assault Raiders, Counter-Raid
       1156:10,1181:8,1143:10,1183:8,1185:8,1182:10,1191:8,1187:10,1174:10,1203:10,1186:8,1184:10,1144:8}   # Engineers + SF/special recon (0.9.4-dev.1, Osama 20 Nov: Snipers, Godswords, Blood Wolves, Falcons, Sea Dragons 8; 0.9.4-dev.4, Osama 21 Nov 'China changes 9.4': Mountain Leopards 8)
def main():
    van=Path(sys.argv[2]);z=zipfile.ZipFile(sys.argv[1]);t={}
    for tab in ('Units','UnitArmorsJson','ArmorsJson'):
        t[tab]={r['Id']:r for r in json.loads((van/(tab+'.json')).read_text())}
        for k,v in json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[tab])).items():
            if v is None:t[tab].pop(int(k),None)
            else:t[tab].setdefault(int(k),{'Id':int(k)}).update(v)
    bad=[]
    for uid,lo in FLOOR.items():
        if uid not in t['Units']:bad.append((uid,'missing card',0,lo));continue
        for ua in (r for r in t['UnitArmorsJson'].values() if r['UnitId']==uid):
            av=t['ArmorsJson'][ua['ArmorId']]['ArmorValue']
            if av<lo:bad.append((uid,t['Units'][uid]['HUDName'],av,lo))
    print('China infantry below their vanilla armour',len(bad));[print(' unit %s %s: ArmorValue %s, needs %s'%b) for b in bad]
    sys.exit(1 if bad else 0)
if __name__=='__main__':main()
