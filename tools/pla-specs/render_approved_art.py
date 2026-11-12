"""Render approved raster masters through native SVG layouts; never regenerate approved designs."""
from pathlib import Path
import argparse,subprocess
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2];tools=root/'tools/pla-specs';out=root/'releases/0.6/source/runtime-qa/icons'
for f in sorted((tools/'approved-patch-masters').glob('*.svg')):
 args=[a.renderer]
 if f.stem.startswith('FA_CHINA_'):args+=['-w','128','-h','128']
 subprocess.run(args+['-o',str(out/(f.stem+'.png')),str(f)],check=True)
for suffix in ['','_OUTLINE']:
 f=tools/'infantry-insignia-vectors'/('FA_PLA_INF_DONGFANG'+suffix+'.svg');subprocess.run([a.renderer,'-o',str(out/(f.stem+'.png')),str(f)],check=True)
print('Rendered approved unit/spec resources; pinned Whistling Arrows PNGs retained unchanged')

# Build27: the native clean-white overrides are the final artwork export.
import sys
if (tools/"white-unit-icons").is_dir():subprocess.run([sys.executable,str(tools/"render_white_unit_icons.py"),"--renderer",a.renderer],check=True)

# Sam2026-11-11: exact supplied China flag is canonical; never regenerate it.
import shutil
shutil.copy2(tools/"approved-country-flags/china.png",out/"FA_CHINA_FLAG.png")
