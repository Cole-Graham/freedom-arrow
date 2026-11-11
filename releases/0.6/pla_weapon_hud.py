"""Weapon HUD art: detailed native stand-ins and traced/model-derived Chinese profiles."""
import json

def apply(root,t,patches,vanilla):
 tools=root.parents[1]/'tools/pla-specs'; source=root/'source/UserData/FreedomArrow'
 vehicles=json.loads((source/'pla-vehicle-armament.json').read_text()); designers=json.loads((source/'pla-infantry-designer.json').read_text())
 equipment={w['weapon']:w['native_weapon'] for u in vehicles['entries'] for w in u['weapons']}
 designer_ids={u['unit'] for u in designers['entries']}
 infantry={r['WeaponId'] for r in t['SquadWeaponsJson'].values() if r['UnitId'] in designer_ids}
 inf_sources={int(k):v for k,v in designers['weapon_sources'].items()}
 available={n.casefold() for n in json.loads((tools/'native-weapon-art-index.json').read_text())['textures']}
 custom={'QBZ-191':'QBZ191','QBZ-192':'QBZ191','QBU-191':'QBU191','QLU-11':'QLU11','QTS-11':'QTS11','QTS-11 grenade launcher':'QTS11','QBZ-95':'QBZ95','QBZ-97':'QBZ97','QBB-95':'QBB95','QBU-88':'QBU88'}
 overrides={'PL-15':'AMRAAM_MISSILE','PL-15 (prototype loadout)':'AMRAAM_MISSILE','PL-12':'AMRAAM_MISSILE','PL-10':'AIM_9X_MISSILE','YJ-18 cruise missiles':'TOMAHAWK_MISSILE','KD-20':'TOMAHAWK_MISSILE','73 mm low-pressure gun':'2A28_GROM','Prototype 120 mm smoothbore':'M256_ABRAMS','QJY-201':'M240','QJY-201 7.62 mm':'M240','QJY-201 door guns':'M240'}
 entries=[]
 for wid in sorted(set(equipment)|infantry):
  w=t['WeaponsJson'][wid];kind='INFANTRY' if wid in infantry else 'VEHICLE';name=w['HUDName']
  assert w['Name'].startswith('PLA '),(wid,'Shared native definition must never be changed')
  donor=inf_sources.get(wid) if wid in infantry else equipment[wid]
  if name in custom:
   profile=custom[name];address='FA_PLA_WP_'+profile;mode='custom'
   basis='Installed model side contour' if profile in {'QBZ191','QBU191','QLU11','QTS11'} else 'Photo-based vector contour; related-family variants are approximations'
  else:
   assert donor in vanilla['WeaponsJson'],(wid,name,donor)
   address=overrides.get(name,vanilla['WeaponsJson'][donor]['HUDIcon']);profile=None;mode='native';basis='Detailed native stand-in artwork; not an exact Chinese weapon drawing'
   if address=='MALVA':address='2A64_MSTA' # Native table uses an absent MALVA icon; same 152 mm gun family.
   assert address.casefold() in available,(wid,name,address)
  fields={'HUDIcon':address};w.update(fields);patches['WeaponsJson'].setdefault(str(wid),{}).update(fields)
  entries.append({'weapon':wid,'name':name,'scope':kind,'mode':mode,'profile':profile,'address':address,'native_weapon':donor,'basis':basis})
 assert len(equipment)==307 and len(infantry)==44
 profiles=sorted({e['profile'] for e in entries if e['mode']=='custom'})
 receipt={'build':json.loads((root/'pla-specializations-contract.json').read_text())['build'],'scope':'Weapon HUD icons only; portraits, unit icons, ammo, statistics and approved models retained.','entries':entries,'vehicle_weapons':len(equipment),'infantry_weapons':len(infantry),'profiles':profiles,'resources':[a for p in profiles for a in ('FA_PLA_WP_'+p,'FA_PLA_WP_'+p+'_OUTLINE')],'native_icon_entries':sum(e['mode']=='native' for e in entries),'custom_icon_entries':sum(e['mode']=='custom' for e in entries),'native_verified':False,'limits':'Detailed native art is reused for stand-ins. Four mesh profiles and four bullpup reference/family contours are custom. Native HUD sizing and final appearance require game inspection.'}
 (source/'pla-weapon-hud.json').write_text(json.dumps(receipt,indent=2)+'\n');(source/'weapon-hud-references.json').write_bytes((tools/'weapon-hud-references.json').read_bytes())
 return receipt
