"""Prepare the branch draft from the exact complete China-UI candidate, never stale generators."""
from pathlib import Path
import argparse,copy,hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6';sys.path[:0]=[str(ROOT),str(R)]
from pipeline.tables import FIELD_TO_FILE
from pipeline.crypto import aes_decrypt
from pla_specializations import apply
from china_ui import apply as apply_china_ui
from pla_catalogue import apply as apply_catalogue
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',type=Path,required=True);p.add_argument('--vanilla',type=Path,required=True);a=p.parse_args()
c=json.loads((R/'pla-specializations-contract.json').read_text())
with a.base.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==c['base_sha256']
source=R/'source/UserData/FreedomArrow';(source/'constants').mkdir(parents=True,exist_ok=True);effective={};patches={};native_ids={}
with zipfile.ZipFile(a.base) as z:
 compatibility=json.loads(z.read('UserData/FreedomArrow/compatibility.json'))
 for name in ['compatibility.json','reference-schema.json','option-id-migration.json']:(source/name).write_bytes(z.read('UserData/FreedomArrow/'+name))
 for table,digest in compatibility['source_plaintext_sha256'].items():
  raw=aes_decrypt((a.vanilla/(table+'.b64')).read_text());assert hashlib.sha256(raw).hexdigest()==digest
  rows={r['Id']:r for r in json.loads(raw)};native_ids[table]=set(rows);patches[table]=json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[table]))
  for key,fields in patches[table].items():
   if fields is None:rows.pop(int(key),None)
   else:rows.setdefault(int(key),{'Id':int(key)}).update(fields)
  effective[table]=rows
 bodies=json.loads(z.read('UserData/FAModels/infantry-bodies.json'));weapons=json.loads(z.read('UserData/FAModels/infantry-weapons.json'))
 (source/'pla-build.json').write_bytes(z.read('UserData/FreedomArrow/pla-build.json'))
 before_bodies=copy.deepcopy(bodies);before_weapons=copy.deepcopy(weapons)
 if 4 not in effective['CountriesJson']:
  def ui_put(table,uid,fields,why):
   effective[table].setdefault(uid,{'Id':uid}).update(fields);patches[table].setdefault(str(uid),{}).update(fields)
  apply_china_ui(R,effective,ui_put)
 receipt=apply(R,effective,patches,bodies,weapons,native_ids)
 models=json.loads(z.read('UserData/FAModels/models.json'));catalogue=apply_catalogue(R,effective,patches,bodies,weapons,models)
 (R/'source/UserData/FAModels/models.json').write_text(json.dumps(models,indent=2)+'\n')
 receipt['catalogue_new_units']=catalogue['new_units'];receipt['catalogue_entries']=catalogue['entry_count']
 receipt['pool_counts']={str(s['id']):sum(v['SpecializationId']==s['id'] for v in effective['SpecializationAvailabilitiesJson'].values()) for s in c['specs']}
 (ROOT/'tools/pla-specs/effective-preview.json').write_text(json.dumps(effective))
 extra=' || '.join('unitId == '+str(i) for i in catalogue['new_body_units'])
 body_code='namespace FAModels;\ninternal static class InfantryBodyIdentity { internal static bool IsSupported(int unitId) => unitId == 901 || (unitId >= 985 && unitId <= 1027)'+(' || '+extra if extra else '')+'; }\n'
 (R/'experimental-model-loader/InfantryBodyIdentity.cs').write_text(body_code)
 assert bodies[:len(before_bodies)]==before_bodies and weapons[:len(before_weapons)]==before_weapons,'Approved offsets changed'
 for table,rows in patches.items():(source/'constants'/FIELD_TO_FILE[table]).write_text(json.dumps(rows,indent=2)+'\n')
 for name,data in [('infantry-bodies.json',bodies),('infantry-weapons.json',weapons)]:
  out=R/'source/UserData/FAModels'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(data,indent=2)+'\n')
 for pool in effective['SpecializationAvailabilitiesJson'].values():
  assert effective['SpecializationsJson'][pool['SpecializationId']]['CountryId']==effective['Units'][pool['UnitId']]['CountryId']
 visible=[u['Id'] for u in effective['CountriesJson'].values() if not u['Hidden']];assert set(visible)=={1,2,4}
 assert len([s for s in effective['SpecializationsJson'].values() if s['ShowInHangar'] and s['CountryId']==4])==6
 receipt.update(base_sha256=c['base_sha256'],approved_body_rules_preserved=len(before_bodies),approved_weapon_rules_preserved=len(before_weapons),visible_countries=visible)
 build=json.loads((source/'pla-build.json').read_text());build.update(build=c['build'],label='PLA TEST Build '+str(c['build']),china_ui=True,pla_only=c['pla_only'],specializations=[x['id'] for x in c['specs']]);(source/'pla-build.json').write_text(json.dumps(build,indent=2)+'\n')
 (source/'pla-specializations.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({k:v for k,v in receipt.items() if k not in ['new_infantry','existing_units']},indent=2))
