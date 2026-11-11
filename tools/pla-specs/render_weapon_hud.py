"""Render all current weapon-family SVGs to the transparent PNGs used by the HUD."""
import argparse,json,subprocess
from pathlib import Path
from weapon_hud_art import get_profile,svg
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];source=root/'releases/0.6/source';out=source/'runtime-qa/icons'
receipt=json.loads((source/'UserData/FreedomArrow/pla-weapon-hud.json').read_text());seen={}
for e in receipt['entries']:
    key,shape=get_profile(e['name'],e['scope']);assert key==e['profile']
    if key in seen:assert seen[key]==shape,key;continue
    seen[key]=shape;name=e['address'];s=out/(name+'.svg');override=root/'tools/pla-specs/hud-model-vectors'/(name+'.svg');s.write_text(override.read_text() if override.exists() else svg(shape))
    subprocess.run([a.renderer,'-o',str(out/(name+'.png')),str(s)],check=True)
print('Rendered',len(seen),'weapon-family HUD profiles for',len(receipt['entries']),'weapon definitions')
