"""Freedom Arrow 0.9.4-dev.1 batch data over exact 0.9.3 (build 242). Opened by BA Codex thread 1567745029781454889 (Osama, Spetsnaz Alpha stand-off RPG-30).
Batch only: build when Osama or Lateralus say the batch is ready. Other threads: add your sections before the check-mode exit, keep the checks.
"""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source';sys.path[:0]=[str(ROOT),str(REL),str(Path(__file__).parent)]
from pipeline.tables import FIELD_TO_FILE
from pla_graph import Graph
V='0.9.4-dev.1';PREV='0.9.3'
# 0.9.3 (build 242, the playtest released 20 Nov 2026) was built in out/local-093r242.
BASE=json.loads((REL/f'out/local-093r242/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--vanilla',type=Path,required=True);p.add_argument('--check',action='store_true',help='run the checks, write nothing');a=p.parse_args()
base=REL/f'out/local-093r242/FreedomArrow-{PREV}-complete.bamod'
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
O=t['OptionsJson'];SM=t['SquadMembersJson'];WA=t['WeaponAmmunitionsJson'];W=t['WeaponsJson']
# ---------- 1. Spetsnaz Alpha, stand-off loadout: 6 RPG-30 (Osama 20 Nov 2026 13:2x PST, thread 1567745029781454889: "Next patch, we need to give 6 rpg
# -30 to spets alpha stand off loadout"). The stand-off option (1511, Custom_Option_Standoff) swaps in unit 354. Disposable launchers are one round per
# carrier (SquadMembers.SpecialWeaponId x WeaponAmmunitions.Quantity 1, the vanilla pattern), so 6 RPG-30 = 6 carriers: the 4 existing (583, 584, 592,
# 593) plus riflemen 587 and 589 (AK-107, no special weapon). Squad size (14), primaries, cost and the close-quarters loadout (unit 131) stay as they are.
_RPG30=169;_NEW=(587,589)
ok(O[1511]['UIName']=='Custom_Option_Standoff' and O[1511]['ReplaceUnitId']==354 and U[354]['HUDName'].strip()=='Spetsnaz Alpha','stand-off option -> unit 354')
ok(W[_RPG30]['HUDName']=='RPG-30' and W[_RPG30]['Type']==63,'weapon 169 is the disposable RPG-30')
_carr=lambda:sorted(m['Id'] for m in SM.values() if m.get('UnitId')==354 and m.get('SpecialWeaponId')==_RPG30)
ok(_carr()==[583,584,592,593],('RPG-30 carriers before',_carr()))
_wa=[r for r in WA.values() if r.get('UnitId')==354 and r.get('WeaponId')==_RPG30]
ok(len(_wa)==1 and _wa[0]['Quantity']==1,('RPG-30 ammo row',_wa))
_men=sum(1 for m in SM.values() if m.get('UnitId')==354);ok(_men==14,('squad size',_men))
for mid in _NEW:
    ok(SM[mid]['UnitId']==354 and SM[mid]['PrimaryWeaponId']==911 and not SM[mid].get('SpecialWeaponId'),(mid,'AK-107 rifleman without a special weapon'))
    g.put('SquadMembersJson',mid,{'SpecialWeaponId':_RPG30})
ok(_carr()==[583,584,587,589,592,593] and sum(1 for m in SM.values() if m.get('UnitId')==354)==_men,('6 RPG-30 carriers, squad size unchanged',_carr()))
rec['spetsnaz_alpha_standoff_rpg30']={'unit':354,'option':1511,'carriers':[4,6],'new_carriers':list(_NEW),'rounds_per_carrier':1,'cost_unchanged':O[1511].get('Cost')}
# ---------- 2. Tank guns and autocannons hurt infantry less: anti-infantry rounds x0.55 (Osama 20 Nov 2026 14:1x PST, thread 1567745029781454889: "I liked
# how Tanks and IFV damage was before we removed the cover ... Maybe we should just do a % damage reduction for IFVs and etc across the board to match
# that?", "no no hook I'm just saying we go across the db and change all the values", "like tank cannon and autocannons"). Before 0.9.0-dev.44 calm infantry
# in the open took 0.36 + 0.02 x soldiers of a hit (8 men: 52 %; tank HE with IgnoreCover 0.25: about 64 %); 0.55 sits between. Scope: rounds of main guns
# (Weapons.Type 110) and autocannons (114) on deck ground vehicles (Units.Type 4, not artillery/MLRS/mortar/loitering roles 130-133) that can target infantry
# (TargetType bit 2) with PenetrationAtMinRange < 150, i.e. HE/frag/MP; AP, APFSDS and HEAT keep their damage, and so do rounds that can target planes (AA autocannons:
# ZU-23, 57 mm Derivatsiya, JRVG-1 76 mm). Damage is one value for every target, so these
# rounds also do 45 % less to light vehicles and (autocannons) helicopters: accepted by Osama. A round also fired by anything else (infantry, helicopters,
# planes, MG/AGL/AA weapons, artillery) gets a vehicle copy so the other users keep their damage.
_F=0.55;_WT={110,114};_ART={130,131,132,133}
_deck={r['UnitId'] for r in t['SpecializationAvailabilitiesJson'].values()}|{t['SpecializationAvailabilitiesJson'][r['SpecializationAvailabilityId']]['UnitId'] for r in t['TransportAvailabilitiesJson'].values() if r.get('SpecializationAvailabilityId') in t['SpecializationAvailabilitiesJson']}
_veh=lambda u:u is not None and u.get('Type')==4 and u.get('Role') not in _ART
_q=lambda wa:_veh(U.get(wa.get('UnitId'))) and W.get(wa.get('WeaponId'),{}).get('Type') in _WT
A=t['AmmunitionsJson']
_sel=lambda a:a is not None and (a.get('TargetType') or 0)&2 and not (a.get('TargetType') or 0)&16 and (a.get('PenetrationAtMinRange') or 0)<150   # plane-capable (AA gun) rounds keep their damage
_rows=[wa for wa in WA.values() if wa.get('UnitId') in _deck and _q(wa) and _sel(A.get(wa.get('AmmunitionId')))]
_ids=sorted({wa['AmmunitionId'] for wa in _rows})
_users={}
for wa in WA.values():_users.setdefault(wa.get('AmmunitionId'),[]).append(wa)
_before={i:A[i].get('Damage') for i in _ids};_copies={};_inplace=[]
for i in _ids:
    other=[wa for wa in _users[i] if not _q(wa)]
    nd=round((A[i].get('Damage') or 0)*_F,3)
    if other:
        c=g.add('AmmunitionsJson',A[i],{'Name':(A[i].get('Name') or '')+' FA vehicle','Damage':nd});_copies[i]=c
        for wa in _users[i]:
            if _q(wa):g.put('WeaponAmmunitionsJson',wa['Id'],{'AmmunitionId':c})
    else:
        g.put('AmmunitionsJson',i,{'Damage':nd});_inplace.append(i)
ok((len(_ids),len(_rows),len(_copies))==(47,84,0),('scope: 47 rounds on 84 vehicle weapon rows, no copies',len(_ids),len(_rows),len(_copies)))
ok(all(abs((A[_copies.get(i,i)].get('Damage') or 0)-round((_before[i] or 0)*_F,3))<1e-9 for i in _ids),'every selected round x0.55')
ok(all(A[i].get('Damage')==_before[i] for i in _copies),'shared originals keep their damage for the other users')
ok(all(A[wa['AmmunitionId']].get('Damage')==_before.get(wa['AmmunitionId'],A[wa['AmmunitionId']].get('Damage')) for wa in WA.values() if not _q(wa)),'no non-vehicle weapon row changed')
ok(all((A[_copies.get(i,i)].get('PenetrationAtMinRange') or 0)<150 and not (A[_copies.get(i,i)].get('TargetType') or 0)&16 for i in _ids),'no AP/HEAT or AA round touched')
ok(not any(_q(wa) and wa['AmmunitionId'] in _copies for wa in WA.values()),'vehicle rows now point at the copies')
rec['vehicle_anti_infantry_x055']={'factor':_F,'rounds':len(_ids),'in_place':len(_inplace),'vehicle_copies':{str(k):v for k,v in _copies.items()},'weapon_rows':len(_rows),
  'examples':{A[i]['HUDName']:[_before[i],A[_copies.get(i,i)]['Damage']] for i in _ids[:12]}}
# ---------- 3. China special forces and line infantry armour (Osama 20 Nov 2026 15:xx PST, thread 1567745029781454889: "PLAAF Snipers have SF cqc kit,
# they need 8 armor and only 1 smoke like other sniper teams. Godswords, BloodWolvse, Falcons, Sea dragons 8 armor 1 smoke. Troopers and light riflement and
# moto riflemen need 8 armor."). ArmorValue 10 -> 8 (SF) and 6 -> 8 (spec 21 line infantry: Moto. Riflemen, Light Riflemen, AA and AT Troopers); HP stays.
# Own armour rows change in place. Godswords use vanilla row 283 (Elite 12Men, shared with units 113 and 150), so they link the existing vanilla row 314
# (Shock 12Men: the same row with ArmorValue 8). Snipers and Godswords use ability 81 (Sprint30 Smoke x4); they link the existing row 103 (Sprint30 Smoke:
# the same row with 1 smoke). Blood Wolves, Falcons and Sea Dragons already have 1 smoke.
AR=t['ArmorsJson'];UA=t['UnitArmorsJson'];AB=t['AbilitiesJson'];UAB=t['UnitAbilitiesJson']
_arm=lambda u:[r for r in UA.values() if r.get('UnitId')==u]
_abl=lambda u:[r for r in UAB.values() if r.get('UnitId')==u]
_same=lambda x,y,skip:all(x.get(k)==y.get(k) for k in set(x)|set(y) if k not in skip)
_OWN={1144:(2012047,10),1183:(2013150,10),1185:(2013216,10),1191:(2013404,10),1196:(2013556,6),1205:(2013818,6),1197:(2013583,6),1198:(2013610,6)}
_names={1144:'Snipers',1181:'Godswords',1183:'Blood Wolves',1185:'Falcons',1191:'Sea Dragons',1196:'Moto. Riflemen',1205:'Light Riflemen',1197:'AA Troopers',1198:'AT Troopers'}
for u,n in _names.items():ok(U[u]['HUDName'].startswith(n) and U[u].get('CountryId')==4 and len(_arm(u))==1,(u,n,'China infantry with one armour row'))
_hp={u:AR[_arm(u)[0]['ArmorId']].get('MaxHealthPoints') for u in _names}
for u,(aid,av) in _OWN.items():
    ok(_arm(u)[0]['ArmorId']==aid and AR[aid].get('ArmorValue')==av and sum(1 for r in UA.values() if r.get('ArmorId')==aid)==1,(u,'own armour row',aid,av))
    g.put('ArmorsJson',aid,{'ArmorValue':8})
ok(_arm(1181)[0]['ArmorId']==283 and _same(AR[283],AR[314],{'Id','Name','ArmorValue','IsDefault'}) and AR[314].get('ArmorValue')==8,'Godswords: row 314 = row 283 with ArmorValue 8')
g.put('UnitArmorsJson',_arm(1181)[0]['Id'],{'ArmorId':314})
ok(_same(AB[81],AB[103],{'Id','Name','SmokeAmmunitionQuantity'}) and (AB[81]['SmokeAmmunitionQuantity'],AB[103]['SmokeAmmunitionQuantity'])==(4,1),'ability 103 = ability 81 with 1 smoke')
for u in (1144,1181):
    r=[x for x in _abl(u) if x.get('AbilityId')==81];ok(len(r)==1,(u,'one Sprint30 Smoke x4 row'));g.put('UnitAbilitiesJson',r[0]['Id'],{'AbilityId':103})
ok(all(AR[_arm(u)[0]['ArmorId']].get('ArmorValue')==8 for u in _names),'all nine units ArmorValue 8')
ok(all(AR[_arm(u)[0]['ArmorId']].get('MaxHealthPoints')==_hp[u] for u in _names),'health points unchanged')
_smk=lambda u:sum(AB[x['AbilityId']].get('SmokeAmmunitionQuantity') or 0 for x in _abl(u))
ok(all(_smk(u)==1 for u in (1144,1181,1183,1185,1191)),'SF and Snipers: 1 smoke')
ok(AR[283].get('ArmorValue')==10 and sorted(r['UnitId'] for r in UA.values() if r.get('ArmorId')==283)==[113,150],'vanilla row 283 unchanged for units 113 and 150')
rec['china_infantry_armor_8']={'units':{str(u):_names[u] for u in _names},'armor_value':8,'godswords_armor_row':[283,314],'smoke_1_ability_row':[81,103],'linked_ability_units':[1144,1181]}
rec['verified']='data checks only'
if a.check:print('checks',checks,'(check only, nothing written)');sys.exit(0)
rec.update(version=V,base=PREV,base_sha256=BASE,checks=checks,verified='data checks only')
def save(n,d):f=SRC/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes((json.dumps(d,indent=2,ensure_ascii=z.read(n).isascii() if n in z.namelist() else False)+'\n').encode())
for tab,fn in FIELD_TO_FILE.items():save('UserData/FreedomArrow/constants/'+fn,patches[tab])
save(f'UserData/FreedomArrow/pla-{V}.json',rec);(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
print('checks',checks)
