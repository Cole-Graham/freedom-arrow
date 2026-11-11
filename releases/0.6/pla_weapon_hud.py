"""Weapon HUD art only: no unit art, ammunition, stats, loadouts or rig changes."""
import json,sys
from pathlib import Path

def apply(root,t,patches):
    tools=root.parents[1]/'tools/pla-specs';sys.path.insert(0,str(tools))
    from weapon_hud_art import get_profile
    source=root/'source/UserData/FreedomArrow'
    vehicles=json.loads((source/'pla-vehicle-armament.json').read_text())
    designers=json.loads((source/'pla-infantry-designer.json').read_text())
    equipment={w['weapon'] for u in vehicles['entries'] for w in u['weapons']}
    designer_ids={u['unit'] for u in designers['entries']}
    infantry={r['WeaponId'] for r in t['SquadWeaponsJson'].values() if r['UnitId'] in designer_ids}
    entries=[]
    for wid in sorted(equipment|infantry):
        w=t['WeaponsJson'][wid];kind='INFANTRY' if wid in infantry else 'VEHICLE'
        assert w['Name'].startswith('PLA '),(wid,'Shared vanilla definition must never be changed')
        profile,_=get_profile(w['HUDName'],kind);key='FA_PLA_WP_'+profile
        fields={'HUDIcon':key};w.update(fields);patches['WeaponsJson'].setdefault(str(wid),{}).update(fields)
        entries.append({'weapon':wid,'name':w['HUDName'],'scope':kind,'profile':profile,'address':key})
    assert len(equipment)==307 and len(infantry)==44
    receipt={'build':json.loads((root/'pla-specializations-contract.json').read_text())['build'],
             'scope':'Weapon HUD icons only. Unit portraits/thumbnails, ammunition icons and all gameplay fields retained.',
             'entries':entries,'vehicle_weapons':len(equipment),'infantry_weapons':len(infantry),
             'profiles':sorted({e['profile'] for e in entries}),'native_verified':False,
             'limits':'Simplified recognition silhouettes. Related variants share physical-family art. Prototype/unnamed analog weapons use recorded family approximations; exact variant geometry is not established.'}
    (source/'pla-weapon-hud.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (source/'weapon-hud-references.json').write_bytes((tools/'weapon-hud-references.json').read_bytes())
    return receipt
