"""Extract CMO DB3K_519 loadouts for each PLA aircraft (fuel tanks, pods and decoys removed)."""
import sqlite3,json,sys
DB='/home/sam/tars/work/ba-dev/replicas/codex/work/pla-cmo-20261112/db/DB3K_519.db3'
c=sqlite3.connect('file:'+DB+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
WT={r[0]:r[1] for r in c.execute('select ID,Description from EnumWeaponType')}
ROLE={r[0]:r[1] for r in c.execute('select ID,Description from EnumLoadoutRole')}
# mod unit -> CMO aircraft ID (latest matching variant); stealth=internal only
MAP={915:(5013,1),916:(8052,0),917:(7658,0),918:(7421,0),919:(7135,0),921:(4454,1),923:(7405,0),924:(7203,0),929:(8053,1),943:(7139,0),944:(8054,1),
     946:(4725,0),955:(7197,0),966:(5454,1),967:(4963,1),971:(7423,1),974:(4817,0),975:(2471,0),977:(4632,0),1089:(7140,0),1091:(5435,0),1092:(2477,0),
     1226:(4633,0),1241:(7188,0),1242:(4039,0),913:(7346,0),914:(7326,0),940:(7417,0),1103:(7417,0),1236:(7417,0),941:(7343,0),942:(4717,0),978:(7416,0),1239:(7416,0),
     1104:(7168,0),1106:(7340,0),1107:(7348,0),1238:(7323,0),1243:(4882,0),1244:(7360,0),1245:(5434,0),1132:(7417,0),1134:(7417,0),1237:(7417,0),1133:(7343,0),1135:(7168,0)}
SKIP_ROLES={1001,9001,9002,9003,9004,9005,7101,7102,7201,8001,8101,8102,8103,4002,4003,4101,4102,4201,4202,4301,6001,6002}
DROP_TYPES=('Fuel','Pod','Decoy','Sonobuoy','Dispenser','Chaff','Flare','Drop Tank','Bathy','Dipping','Cargo','Torpedo','Mine','Laser Designator','Sensor')
out={}
for uid,(aid,stealth) in MAP.items():
  a=c.execute('select ID,Name,YearCommissioned from DataAircraft where ID=?',(aid,)).fetchone()
  los=[];seen=set()
  for l in c.execute('select L.* from DataAircraftLoadouts AL join DataLoadout L on L.ID=AL.ComponentID where AL.ID=? order by L.ID',(aid,)):
    if l['LoadoutRole'] in SKIP_ROLES:continue
    ws=[];bad=False
    for w in c.execute('select LW.Internal,LW.Optional,WR.DefaultLoad,W.ID,W.Name,W.Type from DataLoadoutWeapons LW join DataWeaponRecord WR on WR.ID=LW.ComponentID join DataWeapon W on W.ID=WR.ComponentID where LW.ID=?',(l['ID'],)):
      t=WT.get(w['Type'],str(w['Type']))
      if any(k.lower() in (t+' '+w['Name']).lower() for k in DROP_TYPES):continue
      if 'Gun' in t or 'Cannon' in t:continue
      if stealth and not w['Internal']:bad=True;break
      ws.append({'weapon':w['Name'],'cmo_id':w['ID'],'type':t,'count':w['DefaultLoad'],'internal':bool(w['Internal'])})
    if bad or not ws:continue
    key=tuple(sorted((x['weapon'],x['count']) for x in ws))
    if key in seen:continue
    seen.add(key);los.append({'loadout':l['Name'],'role':ROLE.get(l['LoadoutRole']),'weapons':ws})
  out[uid]={'cmo_id':aid,'cmo_name':a['Name'],'year':a['YearCommissioned'],'stealth_internal_only':bool(stealth),'loadouts':los}
json.dump(out,open(sys.argv[1],'w'),indent=1)
for uid,v in out.items():print(uid,v['cmo_name'],len(v['loadouts']))
