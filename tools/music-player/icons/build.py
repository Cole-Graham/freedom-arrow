from pathlib import Path
import math
r=Path(__file__).resolve().parent;r.mkdir(exist_ok=True)
def star(x,y,rr,color='#fff',rot=-90):
 pts=[]
 for i in range(10):
  a=math.radians(rot+i*36);v=rr if i%2==0 else rr*.382
  pts.append(f'{x+math.cos(a)*v:.3f},{y+math.sin(a)*v:.3f}')
 return f'<polygon points="{" ".join(pts)}" fill="{color}"/>'
usa=''.join(f'<rect y="{i*100/13}" width="190" height="{100/13+.1}" fill="{chr(35)}{("b22234" if i%2==0 else "ffffff")}"/>' for i in range(13))+'<rect width="76" height="53.846" fill="#3c3b6e"/>'
for row in range(9):
 for c in range(6 if row%2==0 else 5):usa+=star(6.33+c*12.67+(6.33 if row%2 else 0),5.38+row*5.38,3.2)
china='<rect width="190" height="100" fill="#de2910"/>'+star(30,26,15,'#ffde00')
for x,y in [(54,10),(65,23),(65,40),(54,53)]:china+=star(x,y,5,'#ffde00',math.degrees(math.atan2(26-y,30-x)))
russia=''.join(f'<rect y="{i*100/3}" width="190" height="34" fill="{c}"/>' for i,c in enumerate(['#fff','#0039a6','#d52b1e']))
rangers='<path d="M8 18 Q95 -7 182 18 L176 70 Q95 48 14 70 Z" fill="#141712" stroke="#b7a566" stroke-width="5"/><text x="95" y="38" fill="#d9c790" text-anchor="middle" font-family="DejaVu Sans" font-size="22" font-weight="bold">3 / 75 RANGER</text><path d="M54 64 L136 64 L136 93 L54 93 Z" fill="#141712" stroke="#b7a566" stroke-width="3"/><text x="95" y="84" fill="#d9c790" text-anchor="middle" font-family="DejaVu Sans" font-size="14" font-weight="bold">RANGERS</text>'
game='<g fill="none" stroke="#c9d9bd" stroke-width="6"><path d="M77 70 V24 L124 15 V61 M77 35 L124 26"/><ellipse cx="66" cy="74" rx="13" ry="9"/><ellipse cx="113" cy="65" rx="13" ry="9"/></g>'
import cairosvg
for name,body in [('usa',usa),('china',china),('russia',russia),('rangers',rangers),('game',game)]:
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="380" height="200" viewBox="0 0 190 100">{body}</svg>'
 (r/(name+'.svg')).write_text(svg);cairosvg.svg2png(bytestring=svg.encode(),write_to=str(r/(name+'.png')),output_width=760,output_height=400)
