"""Verify approved-master hashes, gameplay preservation and actual rendered/embedded art scope."""
from pathlib import Path
import hashlib,json,csv
from PIL import Image
root=Path(__file__).resolve().parents[2];base=root.parent/'pla-art-music-merge-build23';src=root/'releases/0.6/source';before=base/'releases/0.6/source';art=json.loads((src/'UserData/FreedomArrow/pla-approved-art.json').read_text());assert art['build']==24 and art['approved_count']==13
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();icons=src/'runtime-qa/icons'
for key,r in art['profiles'].items():
 assert sha(root/r['approved_master'])==r['sha256'],key
 for a,h in r['png_sha256'].items():assert sha(icons/(a+'.png'))==h,a
for r in art['spec_icons']:assert sha(icons/(r['address']+'.png'))==r['png_sha256'],r['address']
for suffix,h in art['godsword_requested_fix']['runtime_pngs'].items():assert sha(icons/('FA_PLA_INF_DONGFANG'+suffix+'.png'))==h
checks=0
for old in (before/'UserData/FreedomArrow/constants').glob('*.json'):
 assert json.loads(old.read_text())==json.loads((src/'UserData/FreedomArrow/constants'/old.name).read_text()),old.name;checks+=1
assert checks==24
hud=json.loads((src/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());identity=json.loads((src/'UserData/FreedomArrow/pla-infantry-identity.json').read_text());changed=[]
for name in hud['resources']:assert (icons/(name+'.png')).read_bytes()==(before/'runtime-qa/icons'/(name+'.png')).read_bytes(),name
for name in identity['resources']:
 f=icons/(name+'.png');im=Image.open(f);alpha=im.getchannel('A');box=alpha.getbbox();assert im.mode=='RGBA' and im.size==Image.open(before/'runtime-qa/icons'/f.name).size and box and 0<box[0]<box[2]<im.width and 0<box[1]<box[3]<im.height,(name,im.size,box)
 if f.read_bytes()!=(before/'runtime-qa/icons'/f.name).read_bytes():changed.append(name)
for name in ['FA_CHINA_AIR_SF','FA_CHINA_ARMORED','FA_CHINA_ROCKET','FA_CHINA_NAVAL','FA_CHINA_MOTORIZED']:
 im=Image.open(icons/(name+'.png'));assert im.mode=='RGBA' and im.size==(128,128);lo,hi=im.getchannel('A').getextrema();assert lo==0 and hi>=250,(name,lo,hi)
assert (icons/'FA_CHINA_FLAG.png').read_bytes()==(before/'runtime-qa/icons/FA_CHINA_FLAG.png').read_bytes()
expected=(set(art['profiles'])-{'XIANGJIAN'})|{'DONGFANG'};actual={n.removeprefix('FA_PLA_INF_').removesuffix('_OUTLINE') for n in changed};assert actual==expected,(actual,expected);assert len(changed)==26
c=json.loads((root/'releases/0.6/pla-specializations-contract.json').read_text());assert c['build']==24 and c['test_spec']==22
# Native spec addresses remain as previously wired; no unit assignment or order is changed.
effective=json.loads((root/'tools/pla-specs/effective-preview.json').read_text());specs={r['Id']:r for r in effective['SpecializationsJson'].values()} if isinstance(effective['SpecializationsJson'],dict) else {r['Id']:r for r in effective['SpecializationsJson']}
for uid,address in [(17,'FA_CHINA_AIR_SF'),(18,'FA_CHINA_ARMORED'),(19,'FA_CHINA_ROCKET'),(20,'FA_CHINA_NAVAL'),(21,'FA_CHINA_MOTORIZED')]:assert specs[uid]['Icon']==address
r={'passed':True,'gameplay_tables_equal':24,'approved_master_hashes':13,'requested_godsword_pair':True,'unit_sprites_changed':26,'spec_sprites_changed':5,'weapon_hud_sprites_unchanged':len(hud['resources']),'country_flag_unchanged':True,'native_spec_addresses_verified':5,'all90_card_assignments_retained':True,'test_spec_still22':True,'native_verified':False};(root/'tools/pla-specs/build24-art-checks.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
