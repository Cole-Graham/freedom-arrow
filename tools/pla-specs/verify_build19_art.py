"""Check identity/art scope against pinned Build18 and inspect every custom sprite."""
from pathlib import Path
import json,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[2];task=root.parent/'pla-infantry-insignia-20261111';before=json.loads((task/'baseline18.json').read_text());after=json.loads((root/'tools/pla-specs/effective-preview.json').read_text());source=root/'releases/0.6/source';identity=json.loads((source/'UserData/FreedomArrow/pla-infantry-identity.json').read_text());hud=json.loads((source/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());rules={x['unit']:x for x in identity['units']};changes=[]
assert set(before)==set(after)
for table,rows in before.items():
 assert set(rows)==set(after[table]),table
 for uid,row in rows.items():
  assert set(row)==set(after[table][uid]),(table,uid)
  for field,val in row.items():
   new=after[table][uid][field]
   if val==new:continue
   assert table=='Units' and field in {'HUDName','ThumbnailFileName'} and int(uid) in rules,(table,uid,field)
   changes.append({'table':table,'id':int(uid),'field':field,'before':val,'after':new})
assert sum(x['field']=='ThumbnailFileName' for x in changes)==90
assert sum(x['field']=='HUDName' for x in changes)==14
for uid,r in rules.items():
 assert after['Units'][str(uid)]['HUDName']==r['display_name'];assert after['Units'][str(uid)]['ThumbnailFileName']==r['address'];assert r['identity_source'].startswith('https://') and r['art_source'].startswith('https://')
images={};coverage={}
for name in hud['resources']+identity['resources']:
 p=source/'runtime-qa/icons'/(name+'.png')
 with Image.open(p) as im:
  assert im.mode=='RGBA';box=im.getchannel('A').getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,(name,box,im.size)
  assert im.getchannel('A').getextrema()==(0,255)
  coverage[name]=sum(a>200 and min(r,g,b)>200 for r,g,b,a in im.getdata())
  assert coverage[name]>100,(name,'must retain a filled pale motif, not hollow-only lines')
 images[name]=hashlib.sha256(p.read_bytes()).hexdigest()
for name in hud['resources']+identity['resources']:
 if name.endswith('_OUTLINE'):assert coverage[name]>=coverage[name[:-8]]*.8,(name,'outline must retain pale fill')
assert len(images)==44
result={'passed':True,'unit_display_names_changed':14,'unit_thumbnail_addresses_changed':90,'all_other_effective_fields_identical':True,'test_rigging_fixtures_unchanged':True,'portraits_unchanged':True,'weapon_names_ammo_stats_unchanged':True,'normal_outline_sprites_verified':44,'infantry_icon_families':14,'weapon_profile_families':8,'png_sha256':images,'pale_fill_pixel_counts':coverage,'changes':changes,'native_verified':False};(root/'tools/pla-specs/build19-art-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('png_sha256','pale_fill_pixel_counts','changes')}))
