"""Create labelled vector preview sheets from the editable weapon drawings."""
import argparse,html,json,subprocess
from pathlib import Path
from weapon_hud_art import get_profile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--renderer',required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
root=Path(__file__).resolve().parents[2];data=json.loads((root/'releases/0.6/source/UserData/FreedomArrow/pla-weapon-hud.json').read_text());entries={}
for e in data['entries']:entries.setdefault(e['profile'],e)
for page in range((len(entries)+35)//36):
 rows=list(entries.values())[page*36:(page+1)*36];width=1560;height=60+((len(rows)+5)//6)*174
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="#19202a"/><text x="24" y="35" fill="#fff" font-family="sans-serif" font-size="24">PLA weapon HUD art — draft preview {page+1}</text>'
 for i,e in enumerate(rows):
  x=(i%6)*260;y=60+(i//6)*174;_,shape=get_profile(e['name'],e['scope']);override=root/'tools/pla-specs/hud-model-vectors'/(e['address']+'.svg')
  if override.exists():raw=override.read_text();shape=raw[raw.index('>')+1:raw.rindex('</svg>')]
  svg+=f'<g transform="translate({x} {y})"><rect x="5" width="250" height="167" rx="6" fill="#283241"/><g fill="#fff" transform="translate(0 -4)">{shape}</g><text x="12" y="154" fill="#b9d6ed" font-family="sans-serif" font-size="14">{html.escape(e["name"][:31])}</text></g>'
 svg+='</svg>';s=a.output/f'weapon-hud-preview-{page+1}.svg';s.write_text(svg);subprocess.run([a.renderer,'-o',str(s.with_suffix('.png')),str(s)],check=True)
print('Preview sheets:',(len(entries)+35)//36)
