"""Check weapon-team thumbnails, wreath-free named SF and strict presentation-only scope."""
from pathlib import Path
import hashlib,json
from PIL import Image
root=Path(__file__).resolve().parents[2];task=root.parent/'pla-sf-emblems-20261111';before=json.loads((task/'baseline19.json').read_text());after=json.loads((root/'tools/pla-specs/effective-preview.json').read_text());src=root/'releases/0.6/source';identity=json.loads((src/'UserData/FreedomArrow/pla-infantry-identity.json').read_text());hud=json.loads((src/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());rules={e['unit']:e for e in identity['units']};changes=[]
assert set(before)==set(after)
for table,rows in before.items():
 assert set(rows)==set(after[table]),table
 for uid,row in rows.items():
  assert set(row)==set(after[table][uid]),(table,uid)
  for f,v in row.items():
   other=after[table][uid][f]
   if other==v:continue
   assert table=='Units' and f=='ThumbnailFileName' and int(uid) in rules,(table,uid,f)
   changes.append({'unit':int(uid),'before':v,'after':other})
weapon=[e for e in rules.values() if e['icon_kind']=='weapon_team'];sf=[e for e in rules.values() if e['icon_kind']=='sf_emblem'];branch=[e for e in rules.values() if e['icon_kind']=='branch_insignia'];assert len(weapon)==59 and len(sf)==14 and len(branch)==17
assert len(changes)==59 and {e['unit'] for e in weapon}=={e['unit'] for e in changes}
native={e['Id']:e for e in json.loads((root.parent/'black-widow-turn-20261110/vanilla/Units.json').read_text())}
for e in weapon:
 assert after['Units'][str(e['unit'])]['ThumbnailFileName']==e['address']
 if e.get('native_donor_unit'):assert native[e['native_donor_unit']]['Type']==2 and native[e['native_donor_unit']]['ThumbnailFileName']==e['address']
 else:assert e['address'] in identity['resources']
provenance={e['profile']:e for e in json.loads((root/'tools/pla-specs/infantry-insignia-vectors/provenance.json').read_text())}
for e in sf:assert not provenance[e['profile']]['wreath'];assert after['Units'][str(e['unit'])]['ThumbnailFileName']==before['Units'][str(e['unit'])]['ThumbnailFileName']
images={}
for name in hud['resources']+identity['resources']:
 p=src/'runtime-qa/icons'/(name+'.png')
 with Image.open(p) as im:
  alpha=im.getchannel('A');box=alpha.getbbox();assert im.mode=='RGBA' and box and box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,(name,im.size,box);assert alpha.getextrema()==(0,255)
 images[name]=hashlib.sha256(p.read_bytes()).hexdigest()
assert len(images)==48
result={'passed':True,'weapon_equipment_team_icons':59,'named_sf_cards_with_wreath_free_emblems':14,'other_branch_cards_retained':17,'unit_thumbnail_changes':59,'all_names_stats_loadouts_ammo_portraits_rigging_and_other_fields_identical':True,'custom_sprites':48,'compiled_sprite_verification':'Separate resource-check project','png_sha256':images,'changes':changes,'native_verified':False};(root/'tools/pla-specs/build20-art-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('png_sha256','changes')}))
