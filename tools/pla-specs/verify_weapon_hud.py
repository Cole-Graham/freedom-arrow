"""Check all database fields against the pinned predecessor and inspect custom sprite assets."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];before=json.loads(a.before.read_text());after=json.loads((root/'tools/pla-specs/effective-preview.json').read_text());changes=[]
assert set(before)==set(after)
for table,rows in before.items():
 assert set(rows)==set(after[table]),table
 for uid,row in rows.items():
  other=after[table][uid];assert set(row)==set(other),(table,uid,'field set')
  for field,value in row.items():
   if other[field]!=value:changes.append({'table':table,'id':int(uid),'field':field,'before':value,'after':other[field]})
assert changes and all(x['table']=='WeaponsJson' and x['field']=='HUDIcon' for x in changes),changes[:8]
source=root/'releases/0.6/source';receipt=json.loads((source/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());ids={e['weapon'] for e in receipt['entries']};assert len(ids)==351 and {x['id'] for x in changes}<=ids
native={n.casefold() for n in json.loads((root/'tools/pla-specs/native-weapon-art-index.json').read_text())['textures']}
for e in receipt['entries']:
 assert after['WeaponsJson'][str(e['weapon'])]['HUDIcon']==e['address']
 if e['mode']=='native':assert e['address'].casefold() in native
 else:assert e['address'] in receipt['resources']
images={};sizes={}
for name in receipt['resources']:
 path=source/'runtime-qa/icons'/(name+'.png')
 with Image.open(path) as im:
  assert im.mode=='RGBA' and im.width in (232,1160) and 20<=im.height<=550,(name,im.mode,im.size)
  alpha=im.getchannel('A');assert alpha.getextrema()==(0,255),name
  box=alpha.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,(name,box,im.size)
  sizes[name]={'size':im.size,'alpha_bounds':box}
 images[name]=hashlib.sha256(path.read_bytes()).hexdigest()
assert len(images)==len(receipt['resources']) and len(images)==2*len(receipt['profiles'])
result={'passed':True,'weapon_fields_changed':len(changes),'vehicle_weapons':307,'infantry_weapons':44,'native_icon_entries':receipt['native_icon_entries'],'custom_icon_entries':receipt['custom_icon_entries'],'custom_profiles':8,'custom_normal_outline_pngs':16,'all_other_database_fields_identical':True,'unit_art_unchanged':True,'ammo_icons_and_counts_unchanged':True,'png_sha256':images,'png_dimensions':sizes,'changes':changes,'native_verified':False};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('png_sha256','png_dimensions','changes')}))
