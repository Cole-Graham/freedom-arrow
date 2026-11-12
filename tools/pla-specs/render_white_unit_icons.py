"""Render clean-white unit SVG overrides after the historical approved-art render.

The original masters stay unchanged. Sources, clipping and white/alpha filters are
stored in white-unit-icons; no bitmap painting or generative redraw is used.
"""
from pathlib import Path
import argparse,subprocess
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer',required=True);a=p.parse_args();r=Path(__file__).resolve().parents[2];src=r/'tools/pla-specs/white-unit-icons';out=r/'releases/0.6/source/runtime-qa/icons';files=sorted(src.glob('*.svg'));assert len(files)==53
for f in files:
 cmd=[a.renderer]
 if f.stem=='FA_CHINA_MOTORIZED':cmd+=['-w','128','-h','128']
 subprocess.run(cmd+['-o',str(out/(f.stem+'.png')),str(f)],check=True)
print('Rendered52unitPNG and1Motorizedspec; originals retained, four service badges unchanged')
