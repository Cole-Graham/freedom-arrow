"""Create editable monochrome unit-card vectors from documented real patch motifs."""
from pathlib import Path
import argparse,json,math,subprocess,hashlib,tempfile
from PIL import Image
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer',required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2];out=root/'tools/pla-specs/infantry-insignia-vectors';out.mkdir(exist_ok=True);icons=root/'releases/0.6/source/runtime-qa/icons';ivory='#e7f7e4';dark='#26332d'
def path(d,fill=ivory,**attrs):return '<path d="'+d+'" fill="'+fill+'" '+ ' '.join(k.replace('_','-')+'="'+str(v)+'"' for k,v in attrs.items())+'/>'
def star(cx,cy,r,inner=None):
 inner=inner or r*.4;points=[(cx+math.sin(i*math.pi/5)*(r if i%2==0 else inner),cy-math.cos(i*math.pi/5)*(r if i%2==0 else inner)) for i in range(10)];return path('M'+'L'.join(f'{x:.2f},{y:.2f}' for x,y in points)+'Z')
def wreath():
 # Discrete leaf lobes retain clear gaps at the native small icon size.
 s='<g stroke="'+ivory+'" stroke-width="2" fill="none"><path d="M123 144 C80 132 57 100 69 56 M133 144 C176 132 199 100 187 56"/></g>'
 for side in [-1,1]:
  for i in range(8):
   ang=(-33+i*15)*math.pi/180;x=128+side*math.cos(ang)*61;y=80+math.sin(ang)*60
   s+=path(f'M{x:.2f} {y+2:.2f} C{x+side*1:.2f} {y-7:.2f} {x+side*5:.2f} {y-13:.2f} {x+side*10:.2f} {y-15:.2f} C{x+side*11:.2f} {y-6:.2f} {x+side*7:.2f} {y:.2f} {x:.2f} {y+2:.2f}Z')

 return s
sword=path('M125 29 L128 12 L131 29 L131 103 L145 107 L144 111 L131 110 L131 128 L125 128 L125 110 L112 111 L111 107 L125 103 Z')
lightning=path('M86 58 L99 82 L93 82 L109 113 L91 95 L96 94 L83 72 L89 74Z')+path('M170 58 L157 82 L163 82 L147 113 L165 95 L160 94 L173 72 L167 74Z')
def wings(y=64):
 d='M121 '+str(y)+' C107 '+str(y+1)+' 88 '+str(y-4)+' 78 '+str(y-12)+' L81 '+str(y-1)+' L100 '+str(y+11)+' L85 '+str(y+7)+' L92 '+str(y+19)+' L115 '+str(y+27)+' L124 '+str(y+18)+'Z'
 return path(d)+f'<g transform="translate(256 0) scale(-1 1)">{path(d)}</g>'+f'<g stroke="{dark}" stroke-width="1.4" fill="none"><path d="M83 {y-1} L109 {y+10} M90 {y+10} L115 {y+18} M173 {y-1} L147 {y+10} M166 {y+10} L141 {y+18}"/></g>'
def canopy(y=52):return path(f'M105 {y+17} C103 {y-12} 153 {y-12} 151 {y+17} L143 {y+14} L136 {y+17} L128 {y+14} L120 {y+17} L113 {y+14}Z')+f'<path d="M128 {y-4} V{y+14} M119 {y-1} Q115 {y+5} 115 {y+14} M137 {y-1} Q141 {y+5} 141 {y+14}" stroke="{dark}" stroke-width="1.5" fill="none"/>'+'<g fill="none" stroke="'+ivory+'" stroke-width="2"><path d="M106 '+str(y+17)+' L124 '+str(y+49)+' M119 '+str(y+17)+' L126 '+str(y+49)+' M137 '+str(y+17)+' L130 '+str(y+49)+' M150 '+str(y+17)+' L132 '+str(y+49)+'"/></g>'
def anchor():return path('M124 38 L132 38 L132 79 L153 79 L153 85 L132 85 L132 117 Q151 112 161 94 L153 95 L164 80 L171 98 L165 96 Q153 125 128 132 Q103 125 91 96 L85 98 L92 80 L103 95 L95 94 Q105 112 124 117 L124 85 L103 85 L103 79 L124 79Z')+f'<circle cx="128" cy="33" r="9" fill="none" stroke="{ivory}" stroke-width="5"/>'
def wolf(cat=False):
 d='M92 53 L99 25 L116 44 L128 40 L140 44 L157 25 L164 53 L159 87 L147 111 L128 126 L109 111 L97 87Z' if not cat else 'M94 59 Q88 47 91 39 L103 35 L114 45 Q128 41 142 45 L153 35 L165 39 Q168 47 162 59 L166 78 L159 99 L144 118 L128 125 L112 118 L97 99 L90 78 Z'
 s=path(d);s+=path('M99 64 L121 70 L116 76 L103 72Z M157 64 L135 70 L140 76 L153 72Z M118 82 L138 82 L133 91 L123 91Z M110 96 Q128 100 146 96 L142 112 L134 119 L122 119 L114 112Z',dark)
 s+=path('M116 99 L121 100 L121 110 L118 107Z M135 100 L140 99 L138 107 L135 110Z M121 114 L125 110 L125 117Z M131 110 L135 114 L131 117Z')
 if cat:
  for x,y in [(106,49),(150,49),(101,84),(155,84),(110,91),(146,91),(119,57),(137,57)]:s+=f'<ellipse cx="{x}" cy="{y}" rx="3" ry="2.5" fill="{dark}"/>'
 return s
# These paths are original icon adaptations, not copies of source image pixels.
central={
'AIRBORNE':wings()+canopy()+star(128,84,13),
'GROUND':star(128,55,29)+path('M93 99 L99 94 L154 127 L150 134Z M163 99 L157 94 L102 127 L106 134Z'),
'MARINE':anchor()+star(128,66,15),
'ROCKET':path('M117 108 L117 66 Q121 42 128 32 Q135 42 139 66 L139 108 L147 124 L136 121 L132 130 L124 130 L120 121 L109 124Z')+path('M124 63 L132 63 L132 108 L124 108Z',dark)+star(128,20,10),
'ROCKET_SOF':sword+lightning,
'SOF':sword+path('M144 44 L113 72 L130 72 L114 99 L149 65 L131 65Z'),
'LEISHEN':sword+lightning+wings(50)+canopy(39)+star(128,72,12),
'DONGFANG':path('M96 58 L108 60 L113 51 L126 49 L135 55 L142 44 L151 49 L156 43 L163 55 L153 65 L155 76 L144 84 L141 96 L127 98 L121 108 L112 100 L105 86 L94 83 L90 72Z')+f'<g stroke="{dark}" stroke-width="4">{sword}</g>',
'XIANGJIAN':path('M102 87 Q101 62 128 60 Q155 62 154 87 L147 89 L147 98 L109 98 L109 89Z')+path('M89 62 Q128 38 167 62 L163 66 Q128 47 93 66Z')+path('M125 32 L128 20 L131 32 L130 127 L126 127Z')+f'<path d="M91 64 L128 118 L165 64" stroke="{ivory}" stroke-width="2.7" fill="none"/>',
'TIANLANG':wolf(),
'SNOW_LEOPARD':wolf(True),
'JIAOLONG':f'<g transform="translate(19 27) scale(.85)">{anchor()}</g>'+f'<path d="M144 54 C160 63 142 74 124 69 C95 60 95 96 119 101 C139 106 153 89 140 82 C131 77 121 84 127 91" fill="none" stroke="{ivory}" stroke-width="10" stroke-linecap="round"/>'+path('M136 53 L132 42 L139 44 L138 32 L146 40 L154 35 L151 45 L163 47 L157 52 L164 58 L154 60 L149 67 L142 61 L132 62Z')+path('M107 76 L98 67 L94 69 L101 79 L92 83 L94 87 L108 84Z M142 99 L150 105 L154 102 L148 96 L155 90 L152 87 L143 92Z')+f'<path d="M155 56 Q172 63 168 72 M150 60 Q160 72 154 77" fill="none" stroke="{ivory}" stroke-width="2"/>'+f'<path d="M147 49 L153 49 L150 52Z" fill="{dark}"/>',
'POLICE':path('M128 29 L163 43 L160 92 Q154 118 128 133 Q102 118 96 92 L93 43Z')+path('M128 37 L155 48 L153 91 Q147 111 128 123 Q109 111 103 91 L101 48Z',dark)+star(128,61,21)+path('M108 90 L113 90 L113 84 L119 84 L119 91 L125 91 L125 84 L131 84 L131 91 L137 91 L137 84 L143 84 L143 90 L148 90 L148 103 L108 103Z'),
'PAP':star(128,55,27)+path('M104 103 L152 103 L152 111 L104 111Z M112 87 L119 87 L119 81 L125 81 L125 87 L131 87 L131 81 L137 81 L137 87 L144 87 L144 100 L112 100Z')}
contract=json.loads((root/'tools/pla-specs/infantry-identity-contract.json').read_text());receipt=[]
sf_profiles={r['profile'] for r in contract['units'].values() if r.get('icon_kind')=='sf_emblem'}
for name in contract['profiles']:
 if name.startswith('WPN_'):
  for suffix in ['', '_OUTLINE']:
   key='FA_PLA_INF_'+name+suffix;source=root/'tools/pla-specs/hud-model-vectors'/('FA_PLA_WP_'+name[4:]+suffix+'.svg');target=out/(key+'.svg');target.write_text(source.read_text());subprocess.run([a.renderer,'-o',str(icons/(key+'.png')),str(target)],check=True)
  receipt.append({'profile':name,'method':'Existing approved model-derived weapon contour reused as a unit-card sprite','wreath':False});continue
 d=central[name] if name in sf_profiles else wreath()+central[name];hashes={}
 if name in sf_profiles:
  # Measure the vector render without editing bitmap pixels, then fit the vector emblem itself.
  with tempfile.TemporaryDirectory() as tmp:
   vector=Path(tmp)/'measure.svg';png=Path(tmp)/'measure.png';vector.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="256" height="160">'+d+'</svg>');subprocess.run([a.renderer,'-o',str(png),str(vector)],check=True)
   with Image.open(png) as im:box=im.getchannel('A').getbbox()
  scale=min(188/(box[2]-box[0]),140/(box[3]-box[1]));ox=128-scale*(box[0]+box[2])/2;oy=80-scale*(box[1]+box[3])/2;d=f'<g transform="translate({ox} {oy}) scale({scale})">{d}</g>'

 for outline in [False,True]:
  suffix='_OUTLINE' if outline else '';key='FA_PLA_INF_'+name+suffix
  # Filled pale glyph plus a dark keyline, rather than a hollow line-art replacement.
  body=f'<g stroke="{dark}" stroke-width="1.2" paint-order="stroke fill" stroke-linejoin="round">{d}</g>' if outline else d
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="160" viewBox="0 0 256 160">{body}</svg>\n';target=out/(key+'.svg');target.write_text(svg);subprocess.run([a.renderer,'-o',str(icons/(key+'.png')),str(target)],check=True);hashes[suffix or 'plain']=hashlib.sha256(svg.encode()).hexdigest()
 receipt.append({'profile':name,'method':'Original vector simplification of recorded patch motifs; no photograph pixels copied','wreath':name not in sf_profiles,'source_rules':[u['art_source'] for u in contract['units'].values() if u['profile']==name],'svg_sha256':hashes})
(out/'provenance.json').write_text(json.dumps(receipt,indent=2)+'\n');print('Rendered',len(receipt)*2,'unit-card sprites')
