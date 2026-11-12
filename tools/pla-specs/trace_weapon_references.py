"""Read reference pixels and export their measured boundaries as editable SVG paths.
No modified source bitmap is saved. Reference files remain byte-identical.
"""
from pathlib import Path
import json,shutil,subprocess,hashlib
import argparse
import cv2,numpy as np
from PIL import Image
cv2.setRNGSeed(0)
r=Path(__file__).resolve().parents[2];v=r/'tools/pla-specs/hud-photo-vectors';p=v/'references';out=r/'tools/pla-specs/hud-style-overrides';icons=r/'releases/0.6/source/runtime-qa/icons';args=argparse.ArgumentParser(description=__doc__);args.add_argument('--renderer',required=True);render=args.parse_args().renderer
configs=[('QBZ191_PLAIN','qbz191-plain.webp',(0,210,527,190),False,213),('QBZ191','qbz191-optic.jpg',(230,235,1265,480),True,185),('QBZ192','qbz192.png',(65,60,1045,321),False,None),('QCW05','qcw05.png',(5,27,592,247),True,225)]
carbine=[(80,146),(335,145),(347,154),(367,154),(369,149),(388,149),(390,138),(416,138),(421,127),(618,128),(629,125),(658,123),(663,132),(668,102),(669,75),(747,75),(756,82),(758,105),(749,112),(741,115),(741,126),(762,128),(772,116),(787,118),(797,124),(818,115),(835,120),(849,132),(878,139),(1071,140),(1094,146),(1093,205),(1076,291),(1053,291),(1014,260),(960,232),(915,212),(875,211),(864,213),(858,240),(879,292),(869,305),(836,307),(801,260),(789,228),(771,208),(735,209),(728,234),(703,243),(680,233),(663,211),(640,215),(630,253),(607,313),(625,367),(594,371),(560,349),(599,298),(615,250),(619,212),(602,206),(593,208),(560,210),(550,204),(535,206),(525,215),(509,231),(499,262),(495,339),(485,361),(473,366),(452,362),(447,348),(451,282),(448,245),(433,226),(417,212),(406,204),(391,195),(368,193),(364,184),(345,183),(340,192),(94,193),(82,189)]
proof=[]
for key,ref,roi,right,threshold in configs:
 rgb=np.asarray(Image.open(p/ref).convert('RGB'));height,width=rgb.shape[:2];x,y,w,h=roi
 # Pixel analysis only: isolate foreground; final output is SVG geometry.
 if threshold:
  fg=(rgb.max(axis=2)<threshold).astype(np.uint8)
  domain=np.zeros_like(fg);domain[y:y+h,x:x+w]=1
  if key=='QBZ191':
   # Exclude the CAD UI and floor shadow with generous regions outside the weapon.
   domain[:347,:520]=0
   for a,b,limit in [(230,480,550),(480,625,637),(625,725,520),(725,915,708),(915,977,454),(977,1062,640),(1062,1181,450),(1181,1495,431)]:domain[limit:,a:b]=0
  fg*=domain
 else:
  approx=np.zeros((height,width),np.uint8);cv2.fillPoly(approx,[np.array(carbine,np.int32)],1)
  kernel=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(91,91));wide=cv2.dilate(approx,kernel);core=cv2.erode(approx,kernel)
  mask=np.where(wide,cv2.GC_PR_BGD,cv2.GC_BGD).astype(np.uint8);mask[approx>0]=cv2.GC_PR_FGD;mask[core>0]=cv2.GC_PR_FGD
  # Only measured interior points are hard foreground. The broad contour is not trusted as an edge.
  for sx,sy in [(180,169),(270,169),(460,168),(543,171),(640,174),(720,172),(808,171),(928,157),(1030,159),(1073,205),(849,267),(480,294),(710,87),(684,239),(666,284),(646,330),(646,348)]:cv2.circle(mask,(sx,sy),7,cv2.GC_FGD,-1)
  # The dark magazine and stock frame need interior seeds; their outer edges remain unknown.
  for polygon in [[(657,211),(723,211),(716,244),(704,275),(688,307),(667,340),(649,363),(595,335),(613,309),(631,277),(642,247),(650,220)],[(930,202),(1068,278),(1063,284),(927,211)],[(1075,176),(1083,178),(1070,266),(1065,263)],[(470,229),(490,230),(486,355),(475,357)]]:cv2.fillPoly(mask,[np.array(polygon,np.int32)],cv2.GC_FGD)
  cv2.fillPoly(mask,[np.array([(955,190),(1052,184),(1044,237),(1013,217),(974,199)],np.int32)],cv2.GC_BGD)
  cv2.grabCut(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),mask,None,np.zeros((1,65)),np.zeros((1,65)),12,cv2.GC_INIT_WITH_MASK);fg=np.isin(mask,[cv2.GC_FGD,cv2.GC_PR_FGD]).astype(np.uint8)
 n,labels,stats,_=cv2.connectedComponentsWithStats(fg,8);largest=1+int(np.argmax(stats[1:,cv2.CC_STAT_AREA]));fg=np.isin(labels,[i for i in range(1,n) if stats[i,cv2.CC_STAT_AREA]>=500]).astype(np.uint8) if key=='QBZ192' else (labels==largest).astype(np.uint8)
 contours,hierarchy=cv2.findContours(fg,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE);paths=[];kept=[]
 for c in contours:
  area=cv2.contourArea(c)
  if area<max(2,w*w*.000002):continue
  q=cv2.approxPolyDP(c,.45,True).reshape(-1,2)
  if len(q)<3:continue
  paths.append('M'+'L'.join(f'{a},{b}' for a,b in q)+'Z');kept.append(q)
 d=' '.join(paths);ys,xs=np.where(fg);bx,by,bw,bh=int(xs.min()),int(ys.min()),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1);pad=max(2,bw*.01);view=(bx-pad,by-pad,bw+2*pad,bh+2*pad);vx,vy,vw,vh=view;stroke=1.25*vw/232
 # Internal hardware line segments are measured from the same reference, not invented.
 gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY);detector=cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD);lines=detector.detect(gray)[0];inside=cv2.erode(fg,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5)));segments=[]
 if lines is not None:
  for line in lines.reshape(-1,4):
   a,b,c,e=map(float,line);length=((c-a)**2+(e-b)**2)**.5
   if length<vw*.004 or length>vw*.45:continue
   samples=[(round(a+(c-a)*t),round(b+(e-b)*t)) for t in (0,.25,.5,.75,1)]
   if not all(0<=sx<width and 0<=sy<height and inside[sy,sx] for sx,sy in samples):continue
   segments.append((length,f'M{a:.2f} {b:.2f}L{c:.2f} {e:.2f}'))
 segments=sorted(segments,reverse=True)[:350 if key=='QBZ191' else 180];detail=' '.join(x[1] for x in segments)
 mirror=f'transform="translate({2*vx+vw:g} 0) scale(-1 1)"' if right else ''
 common=f'viewBox="{vx:g} {vy:g} {vw:g} {vh:g}"';svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="{1160*vh/vw:.3f}" {common}><g {mirror}><path id="measured-boundary" fill="#65706b" fill-opacity="0.9" fill-rule="evenodd" stroke="#fff" stroke-width="{stroke:g}" stroke-linejoin="round" d="{d}"/><path fill="none" stroke="#cdd8d0" stroke-opacity="0.7" stroke-width="{vw/232*.55:g}" stroke-linecap="round" d="{detail}"/></g></svg>'
 f=v/('FA_PLA_WP_'+key+'.svg');f.write_text(svg+'\n')
 for suffix in ['','_OUTLINE']:
  name='FA_PLA_WP_'+key+suffix;dest=out/(name+'.svg');dest.write_text(svg+'\n');subprocess.run([render,'-o',str(icons/(name+'.png')),str(dest)],check=True)
 overlay=f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw:g}" height="{vh:g}" {common}><image width="{width}" height="{height}" href="references/{ref}"/><path fill="none" fill-rule="evenodd" stroke="#00ffff" stroke-width="{max(1,vw/500):g}" d="{d}"/></svg>';f=v/('overlay-'+key+'.svg');f.write_text(overlay);subprocess.run([render,'-o',str(p/('edge-check-'+key+'.png')),str(f)],check=True)
 proof.append({'profile':key,'reference':ref,'reference_sha256':hashlib.sha256((p/ref).read_bytes()).hexdigest(),'method':'Source pixel segmentation → measured contour → editable SVG; internal measured line segments','boundary_simplification_max_parameter_px':.45,'boundary_vertices':sum(len(q) for q in kept),'internal_measured_segments':len(segments),'raster_width':1160,'source_boundary_box':[bx,by,bw,bh],'source_faces_right':right,'native_direction':'muzzle right after native HUD mirror','edge_overlay':'edge-check-'+key+'.png'})
(p/'edge-trace-proof.json').write_text(json.dumps(proof,indent=2)+'\n');(v/'references.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
