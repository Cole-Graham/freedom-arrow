"""Verify shortEnglish labels, explicit line-vs-specialist policy and presentation-only scope."""
from pathlib import Path
from collections import Counter
import json,hashlib
from PIL import Image
root=Path(__file__).resolve().parents[2];task=root.parent/'pla-detailed-infantry-icons-20261111';before=json.loads((task/'baseline20.json').read_text());after=json.loads((root/'tools/pla-specs/effective-preview.json').read_text());src=root/'releases/0.6/source';c=json.loads((root/'tools/pla-specs/infantry-identity-contract.json').read_text());identity=json.loads((src/'UserData/FreedomArrow/pla-infantry-identity.json').read_text());hud=json.loads((src/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());rules={e['unit']:e for e in identity['units']};changes=[]
assert set(before)==set(after)
for table,rows in before.items():
 assert set(rows)==set(after[table]),table
 for uid,row in rows.items():
  assert set(row)==set(after[table][uid]),(table,uid)
  for f,v in row.items():
   other=after[table][uid][f]
   if other==v:continue
   assert table=='Units' and f in ['HUDName','ThumbnailFileName'] and int(uid) in rules,(table,uid,f)
   changes.append({'unit':int(uid),'field':f,'before':v,'after':other})
counts=Counter(e['icon_kind'] for e in rules.values());assert counts=={'weapon_team':54,'sf_emblem':14,'line_patch':17,'branch_insignia':5},counts
assert Counter(x['field'] for x in changes)=={'HUDName':14,'ThumbnailFileName':22}
assert after['Units']['1181']['HUDName']=='Godsword'
assert after['Units']['1190']['HUDName']=='Sea Dragons'
assert after['Units']['1191']['HUDName']=='Sea Dragons Recon'
for e in rules.values():
 assert after['Units'][str(e['unit'])]['ThumbnailFileName']==e['address']
 if e['icon_kind']=='sf_emblem':assert not any('\u4e00'<=ch<='\u9fff' for ch in e['display_name'])
for uid in [1158,1159,1167,1175,1179,1198]:assert rules[uid]['icon_kind']=='line_patch'
for uid in [1137,1152,1168,1193]:assert rules[uid]['icon_kind']=='weapon_team'
assert rules[1199]['icon_kind']=='weapon_team'
for uid,p in c['line_patch_policy']['units'].items():assert rules[int(uid)]['profile']==p
images={};bounds={}
for name in hud['resources']+identity['resources']:
 p=src/'runtime-qa/icons'/(name+'.png')
 with Image.open(p) as im:
  alpha=im.getchannel('A');box=alpha.getbbox();assert im.mode=='RGBA' and box and box[0]>0 and box[1]>0 and box[2]<im.width and box[3]<im.height,(name,im.size,box);assert alpha.getextrema()==(0,255);bounds[name]=box
 images[name]=hashlib.sha256(p.read_bytes()).hexdigest()
assert len(images)==64,len(images)
# SVG masks remove dilated foreground shapes from the background, leaving actual alpha gaps.
vectors=root/'tools/pla-specs/infantry-insignia-vectors'
for profile in ['TIANLANG','SNOW_LEOPARD','JIAOLONG','DONGFANG','LEISHEN','XIANGJIAN','SOF']:
 s=(vectors/('FA_PLA_INF_'+profile+'.svg')).read_text();assert '<mask ' in s and 'mask="url(' in s,profile
provenance={e['profile']:e for e in json.loads((vectors/'provenance.json').read_text())}
for e in rules.values():
 if e['icon_kind']=='sf_emblem':assert not provenance[e['profile']]['wreath']
# Prior weaponHUD resources are byte-identical: only the unit-card layer is being changed here.
old=root.parent/'pla-sf-emblems-weapon-teams-build20/releases/0.6/source/runtime-qa/icons'
for name in hud['resources']:assert (src/'runtime-qa/icons'/(name+'.png')).read_bytes()==(old/(name+'.png')).read_bytes()
result={'passed':True,'counts':dict(counts),'display_name_changes':14,'thumbnail_changes':22,'tables_checked':len(before),'all_other_effective_fields_identical':True,'weapon_hud_sprites_byte_identical':True,'custom_sprites':len(images),'real_alpha_cutout_masks':True,'brigade_evidence_limit':c['line_patch_policy']['brigade_evidence_limit'],'png_sha256':images,'alpha_bounds':bounds,'changes':changes,'native_verified':False};(root/'tools/pla-specs/build21-art-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['png_sha256','alpha_bounds','changes']}))
