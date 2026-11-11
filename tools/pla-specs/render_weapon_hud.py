"""Render only approved editable custom contours; native stand-ins use native game addresses."""
import argparse,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];source=root/'releases/0.6/source';out=source/'runtime-qa/icons';receipt=json.loads((source/'UserData/FreedomArrow/pla-weapon-hud.json').read_text())
for address in receipt['resources']:
 choices=[root/'tools/pla-specs'/folder/(address+'.svg') for folder in ['hud-model-vectors','hud-reference-vectors']];found=[p for p in choices if p.exists()];assert len(found)==1,(address,found)
 subprocess.run([a.renderer,'-o',str(out/(address+'.png')),str(found[0])],check=True)
print('Rendered',len(receipt['resources']),'normal/outline sprites for',len(receipt['profiles']),'custom profiles; native stand-ins are resolved by the game')
