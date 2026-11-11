"""Apply only China UI fields to the pinned complete Build4; retain every approved infantry row."""
from pathlib import Path
import argparse,copy,hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6';sys.path[:0]=[str(ROOT),str(R)]
from pipeline.tables import FIELD_TO_FILE
from pipeline.crypto import aes_decrypt
from china_ui import apply
ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True);ap.add_argument('--vanilla',type=Path,required=True);a=ap.parse_args()
def sha_file(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(4*1024*1024):h.update(b)
 return h.hexdigest()
assert sha_file(a.base)=='8eca43e9f4ecd6bfcbb0b4a9ffe666a38d9b5121c66825106669d35c3ca94656'
src=R/'source/UserData/FreedomArrow';effective={};patches={}
with zipfile.ZipFile(a.base) as z:
 compat=json.loads(z.read('UserData/FreedomArrow/compatibility.json'))
 for table,digest in compat['source_plaintext_sha256'].items():
  raw=aes_decrypt((a.vanilla/(table+'.b64')).read_text());assert hashlib.sha256(raw).hexdigest()==digest
  rows={r['Id']:r for r in json.loads(raw)};patches[table]=json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[table]))
  for key,fields in patches[table].items():
   if fields is None:rows.pop(int(key),None)
   else:rows.setdefault(int(key),{'Id':int(key)}).update(fields)
  effective[table]=rows
before=copy.deepcopy(effective)
def put(t,i,fields,why):effective[t].setdefault(i,{'Id':i}).update(fields);patches[t].setdefault(str(i),{}).update(fields)
apply(R,effective,put)
changed={};allowed={'Units':{'CountryId'},'SpecializationAvailabilitiesJson':{'SpecializationId'}}
for t,rows in effective.items():
 for i,row in rows.items():
  old=before[t].get(i)
  if old==row:continue
  fields={f for f in row if old is None or row[f]!=old.get(f)}
  assert t in allowed or t=='CountriesJson' and i==4 or t=='SpecializationsJson' and i in range(17,22),(t,i)
  if t in allowed:assert old is not None and fields<=allowed[t],(t,i,fields)
  changed.setdefault(t,[]).append(i)
assert all(set(before[t])<=set(effective[t]) for t in before)
assert len([r for r in effective['SquadMembersJson'].values() if r['UnitId'] in range(985,1010)])==175
assert sum(not r['Hidden'] for r in effective['CountriesJson'].values())==3
visible=[r for r in effective['SpecializationsJson'].values() if r['ShowInHangar']]
assert len(visible)+3<32,'Native filter bit budget'
for r in visible:assert r['CountryId'] in effective['CountriesJson']
for r in effective['SpecializationAvailabilitiesJson'].values():
 s=effective['SpecializationsJson'][r['SpecializationId']]
 assert s['CountryId']==effective['Units'][r['UnitId']]['CountryId'],('country mismatch',r['Id'])
(src/'constants').mkdir(parents=True,exist_ok=True)
for t,rows in patches.items():(src/'constants'/FIELD_TO_FILE[t]).write_text(json.dumps(rows,indent=2)+'\n')
receipt={'base_sha256':sha_file(a.base),'changed_rows':changed,'approved_infantry_members_preserved':175,'all_non_ui_fields_identical':True,'native_filter_bits':len(visible)+3,'native_verified':False}
(src/'china-ui-checks.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({**receipt,'changed_rows':{t:len(ids) for t,ids in changed.items()}},indent=2))
