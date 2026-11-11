"""Verify weapon-only scope against the previous full effective database and inspect PNGs."""
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
assert len(changes)==351 and all(x['table']=='WeaponsJson' and x['field']=='HUDIcon' for x in changes),changes[:8]
source=root/'releases/0.6/source';receipt=json.loads((source/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());ids={e['weapon'] for e in receipt['entries']};assert ids=={x['id'] for x in changes}
images={}
for e in receipt['entries']:
    name=e['address'];assert after['WeaponsJson'][str(e['weapon'])]['HUDIcon']==name
    if name in images:continue
    path=source/'runtime-qa/icons'/(name+'.png')
    with Image.open(path) as im:
        assert im.mode=='RGBA' and im.size==(256,160),(name,im.mode,im.size)
        alpha=im.getchannel('A');assert alpha.getextrema()==(0,255),name
        box=alpha.getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<256 and box[3]<160,(name,box)
        # All visible pixels must be white, with alpha providing the edge coverage.
        assert all((r,g,b)==(255,255,255) for r,g,b,av in im.getdata() if av>0),name
    images[name]=hashlib.sha256(path.read_bytes()).hexdigest()
result={'passed':True,'weapon_fields_changed':len(changes),'vehicle_weapons':receipt['vehicle_weapons'],'infantry_weapons':receipt['infantry_weapons'],'weapon_family_pngs':len(images),'all_other_database_fields_identical':True,'unit_art_unchanged':True,'ammo_icons_and_counts_unchanged':True,'png_sha256':images,'changes':changes,'native_verified':False};a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('png_sha256','changes')}))
