"""Apply display names and patch-derived unit thumbnails without changing squad designs."""
import json
from pathlib import Path

def apply(root,t,patches):
 tools=root.parents[1]/'tools/pla-specs';source=root/'source/UserData/FreedomArrow';designer=json.loads((source/'pla-infantry-designer.json').read_text());contract=json.loads((tools/'infantry-identity-contract.json').read_text());entries=[]
 for item in designer['entries']:
  uid=item['unit'];rule=contract['units'][str(uid)];u=t['Units'][uid];fields={'HUDName':rule['display_name'],'ThumbnailFileName':rule['address']};u.update(fields);patches['Units'].setdefault(str(uid),{}).update(fields)
  item['source_design_name']=item.get('source_design_name',item['name']);item['name']=rule['display_name'];item['identity']=rule['identity'];item['unit_icon']=rule['address']
  entries.append({'unit':uid,'spec':item['spec'],'source_design_name':item['source_design_name'],**rule})
 receipt={'build':json.loads((root/'pla-specializations-contract.json').read_text())['build'],'scope':'Display names and unit thumbnail icons only; portraits, unit internal names/IDs, squad designs, stats, rigging and all28 appearance fixtures retained.','units':entries,'count':len(entries),'profiles':contract['profiles'],'resources':[a for p in contract['profiles'] for a in ('FA_PLA_INF_'+p,'FA_PLA_INF_'+p+'_OUTLINE')],'native_verified':False,'limits':'Unit identity and patch motifs are sourced separately. Parent-branch and generic SOF badge fallbacks are explicit; no unverified badge is described as a verified exact issued patch. Existing gameplay roles/loadouts do not establish real formation TO&E.'}
 (source/'pla-infantry-designer.json').write_text(json.dumps(designer,indent=2)+'\n');(source/'pla-infantry-identity.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
