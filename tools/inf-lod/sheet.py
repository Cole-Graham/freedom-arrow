"""Before/after sheet: one row per body, LOD0/1/2 before|after, labelled with triangle counts. usage: sheet.py OUT.png BODY..."""
import sys,json
from PIL import Image,ImageDraw
p=json.load(open('plan.json'));out=sys.argv[1];bodies=sys.argv[2:];W,H=300,400
S=Image.new('RGB',(W*6,(H+30)*len(bodies)),'white');d=ImageDraw.Draw(S)
for r,b in enumerate(bodies):
    for l in range(3):
        f=f'{b}_{l}' if b!='PLA_lod' else f'PLA_lod_{l}';v=p[f+'.fas']
        for k,(src,n) in enumerate((('orig',v['before']),('out',v.get('after',v['before'])))):
            try:im=Image.open(f'ren/{f}_{src}.png').resize((W,H))
            except FileNotFoundError:continue
            x=(l*2+k)*W;y=r*(H+30)+30;S.paste(im,(x,y));d.text((x+6,y-24),f"{b[5:] if b.startswith('pla2_') else b} LOD{l} {'before' if k==0 else 'after'}: {n:,} tris",fill='black')
S.save(out)
