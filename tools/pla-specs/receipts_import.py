"""Repo cleanup step 1 (Lateralus 22 Nov 2026): copy the build receipts from out/0.8 and every out/local-* folder into out/receipts, the
one record of builds that package_0_8_next.py reads and writes. Copies only; nothing is moved or deleted. Run again before the cleanup
branch merges, to pick up builds made meanwhile by threads still on the old packager. Stops if one version has two different receipts."""
import hashlib,json,re,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from fa_version import PATTERN
OUT=Path(__file__).resolve().parents[2]/'releases/0.6/out';R=OUT/'receipts';R.mkdir(exist_ok=True)
seen={}
for f in sorted(OUT.glob('*/FreedomArrow-0.*.json')):
    if f.parent==R or not re.fullmatch(r'FreedomArrow-('+PATTERN+r'(?:-[a-z0-9-]+)?)\.json',f.name):continue
    d=json.loads(f.read_text())
    if 'complete' not in d:continue   # not a package receipt
    h=hashlib.sha256(f.read_bytes()).hexdigest()
    if seen.get(f.name,h)!=h:raise SystemExit(f'{f.name}: two different receipts ({seen[f.name][:8]} and {h[:8]}); decide which build is real first')
    seen[f.name]=h
added=0
for name,h in seen.items():
    t=R/name
    if t.exists():
        if hashlib.sha256(t.read_bytes()).hexdigest()!=h:raise SystemExit(f'{name}: out/receipts already holds a different receipt')
        continue
    src=next(f for f in OUT.glob('*/'+name) if f.parent!=R and hashlib.sha256(f.read_bytes()).hexdigest()==h)
    shutil.copy2(src,t);added+=1
print(f'out/receipts: {len(list(R.glob("FreedomArrow-*.json")))} receipts ({added} copied now)')
