"""Rasterize small original, code-drawn UI symbols; no purchased texture or photo is edited."""
from pathlib import Path
import math,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'releases/0.6/source/runtime-qa/icons';OUT.mkdir(parents=True,exist_ok=True)
def star(cx,cy,r,angle=-math.pi/2):
 return [(cx+math.cos(angle+i*math.pi/5)*r*(1 if i%2==0 else .382),cy+math.sin(angle+i*math.pi/5)*r*(1 if i%2==0 else .382)) for i in range(10)]
im=Image.new('RGBA',(768,512),'#de2910');d=ImageDraw.Draw(im)
d.polygon(star(128,128,76.8),fill='#ffde00')
for x,y in [(256,51.2),(307.2,102.4),(307.2,179.2),(256,230.4)]:d.polygon(star(x,y,25.6,math.atan2(128-y,128-x)),fill='#ffde00')
im.resize((384,256),Image.Resampling.LANCZOS).save(OUT/'FA_CHINA_FLAG.png')
WHITE='#d4ded0';s=4
for name in ['AIR_SF','ARMORED','ROCKET','NAVAL','MOTORIZED']:
 im=Image.new('RGBA',(128*s,128*s));d=ImageDraw.Draw(im)
 def line(points,w=6):d.line([(int(x*s),int(y*s)) for x,y in points],fill=WHITE,width=w*s,joint='curve')
 def poly(points):d.polygon([(x*s,y*s) for x,y in points],fill=WHITE)
 def circle(box,w=6):d.ellipse(tuple(x*s for x in box),outline=WHITE,width=w*s)
 if name=='AIR_SF':
  poly([(59,17),(69,17),(72,54),(112,77),(112,86),(72,73),(72,100),(86,110),(86,116),(64,108),(42,116),(42,110),(56,100),(56,73),(16,86),(16,77),(56,54)])
 elif name=='ARMORED':
  line([(23,91),(105,91)],19);line([(19,70),(33,53),(91,53),(108,70),(19,70)],8);line([(53,51),(53,35),(85,35),(85,51)],9);line([(84,40),(119,40)],7)
  for x in [30,52,74,96]:circle((x-7,83,x+7,99),3)
 elif name=='ROCKET':
  poly([(64,10),(83,39),(83,82),(72,82),(72,100),(64,117),(56,100),(56,82),(45,82),(45,39)]);circle((55,39,73,57),4);line([(40,77),(26,101)],6);line([(88,77),(102,101)],6)
 elif name=='NAVAL':
  circle((55,13,73,31),5);line([(64,31),(64,110)],7);line([(35,48),(93,48)],6);line([(22,76),(25,92),(39,108),(64,115),(89,108),(103,92),(106,76)],7);poly([(12,78),(32,78),(23,67)]);poly([(96,78),(116,78),(105,67)])
 else:
  circle((17,17,111,111),8);circle((51,51,77,77),6)
  for a in range(0,360,60):
   q=math.radians(a);line([(64+17*math.cos(q),64+17*math.sin(q)),(64+42*math.cos(q),64+42*math.sin(q))],6)
 im.resize((128,128),Image.Resampling.LANCZOS).save(OUT/('FA_CHINA_'+name+'.png'))
print('Six original UI sprites generated. Flat flag is a temporary reconstruction; supplied photo could not be fetched.')
