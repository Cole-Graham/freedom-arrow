"""Reconstruct effective predecessor rows directly from an exact pinned full package."""
import json,sys,zipfile,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root));from pipeline.tables import FIELD_TO_FILE
archive=Path(sys.argv[1]);out=Path(sys.argv[2]);vanilla=Path(sys.argv[3]);tables={}
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==json.loads((root/'releases/0.6/pla-specializations-contract.json').read_text())['runtime_base_sha256']
with zipfile.ZipFile(archive) as z:
 c=json.loads(z.read('UserData/FreedomArrow/compatibility.json'))
 for table in c['source_plaintext_sha256']:
  rows={str(r['Id']):r for r in json.loads((vanilla/(table+'.json')).read_text())}
  for uid,fields in json.loads(z.read('UserData/FreedomArrow/constants/'+FIELD_TO_FILE[table])).items():
   if fields is None:rows.pop(uid,None)
   else:rows.setdefault(uid,{'Id':int(uid)}).update(fields)
  tables[table]=rows
out.write_text(json.dumps(tables))
