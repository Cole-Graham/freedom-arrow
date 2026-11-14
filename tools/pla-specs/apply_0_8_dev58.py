"""Freedom Arrow 0.8.0-dev.58 over exact 0.8.0-dev.57 (Osama 13 Nov 15:57 PST, thread 1569806740139282476):
"I just downloaded FK-2000 can you check?" The purchased CGTrader FK-2000 (seller GLB with the full PBR set) replaces the old
FK-2000 stand-in model: m_fk2000s, static (not rigged), seller paint, GlassyFK on the vanilla F-16 glass. Converted with
work/pla-0.8/cart-20261113/anyconv.py (no recolour); purchased files stay out of git.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REL=ROOT/'releases/0.6';SRC=REL/'source'
V='0.8.0-dev.58';PREV='0.8.0-dev.57'
BASE=json.loads((REL/f'out/0.8/FreedomArrow-{PREV}.json').read_text())['complete']['sha256']
p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
with (REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==BASE
z=zipfile.ZipFile(REL/f'out/0.8/FreedomArrow-{PREV}-complete.bamod');MJ='UserData/FAModels/models.json';models=json.loads(z.read(MJ))
before=dict(models['PLA FK-2000']);assert before['file']=='m_fk2000_static.fam',before
models['PLA FK-2000']={'file':'m_fk2000s_static.fam','battle':'m_fk2000s_lo_static.fam','align':False}
files=sorted(x.name for x in a.stage.iterdir());assert 'm_fk2000s_static.fam' in files and 'm_fk2000s_lo_static.fam' in files
rec={'version':V,'base':PREV,'base_sha256':BASE,'request':'Osama 13 Nov 15:57 PST: FK-2000 downloaded','models_json':{'PLA FK-2000':{'before':before,'after':models['PLA FK-2000']}},'files':files,'checks':2}
(ROOT/f'tools/pla-specs/{V}-models.json').write_bytes((json.dumps(models,indent=2,ensure_ascii=z.read(MJ).isascii())+'\n').encode())
(SRC/f'UserData/FreedomArrow/pla-{V}.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');(ROOT/f'tools/pla-specs/{V}-checks.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print('ok',len(files))
