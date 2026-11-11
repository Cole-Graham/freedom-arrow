"""Original vector HUD silhouettes, grouped by physical weapon family, not gameplay class.

SVG is the editable source. These are recognition drawings, not dimensional drawings.
Prototypes/unspecified draft weapons retain an explicitly recorded family approximation.
"""
import re

def path(d):return '<path d="'+d+'"/>'
def rect(x,y,w,h):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}"/>'
def circle(x,y,r):return f'<circle cx="{x}" cy="{y}" r="{r}"/>'
def poly(points):return '<polygon points="'+' '.join(f'{x},{y}' for x,y in points)+'"/>'
def holes(shape,d,key):
 return f'<defs><mask id="holes_{key}" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="160"><rect width="256" height="160" fill="white"/><path d="{d}" fill="black"/></mask></defs><g mask="url(#holes_{key})">{shape}</g>'

# Body half-width, nose length, wing start/end/span and tail start/end/span.
# The PL-10 has a rounded seeker dome and long strakes. PL-15 has a pointed
# radome and compact mid-body fins. Red Arrow 10 uses broad folding wings.
MISSILES={
 'PL10':(7,12,80,157,14,26,57,25,'round'),
 'PL15':(8,36,115,145,24,25,51,24,'point'),
 'PL12':(7,33,100,135,28,25,51,26,'point'),
 'PL17':(8,43,113,134,15,25,47,20,'point'),
 'PL8':(7,15,156,185,27,25,70,31,'round'),
 'PL2':(6,15,161,184,18,26,64,25,'round'),
 'R73':(7,17,163,186,23,25,66,30,'round'),
 'HJ10':(10,18,116,146,44,30,51,21,'round'),
 'HJ8':(9,27,73,118,37,27,50,19,'point'),
 'HJ9':(8,32,92,129,31,25,49,20,'point'),
 'HJ73':(11,15,97,131,42,26,49,22,'round'),
 'AKD10':(8,23,97,131,31,27,52,25,'point'),
 'BA7':(7,24,110,143,29,25,49,24,'point'),
 'QN502':(8,25,103,137,33,27,52,22,'point'),
 'QN201':(7,20,105,139,25,26,49,19,'round'),
 'TY90':(7,18,135,167,24,27,55,24,'round'),
 'QW2':(6,18,153,177,19,26,53,19,'round'),
 'HQ7':(8,26,96,135,36,27,53,23,'point'),
 'HQ9':(7,38,88,139,25,24,53,26,'point'),
 'HQ16':(8,32,88,134,35,25,54,26,'point'),
 'HQ17':(7,25,147,175,18,26,65,29,'point'),
 'HQ6':(7,28,89,137,34,25,55,27,'point'),
 'HQ12':(8,35,95,143,35,26,56,28,'point'),
 'HQ11':(7,31,107,141,25,27,56,24,'point'),
 'FB10':(7,23,135,161,22,26,53,23,'point'),
 'FK2000':(6,24,137,164,20,25,53,23,'point'),
 'KD88':(11,32,98,143,34,27,59,32,'round'),
 'KH29':(12,28,107,150,35,28,65,36,'point'),
 'YJ91':(9,36,103,142,24,25,54,24,'point'),
 'KD20':(12,42,92,137,41,26,54,29,'point'),
 'YJ18':(10,34,107,143,36,26,54,27,'point'),
 'SY400':(10,34,0,0,0,26,61,28,'point'),
 'DF15':(12,48,0,0,0,25,65,27,'point'),
 'DF21':(13,48,0,0,0,0,0,0,'point'),
 'DF31':(15,45,0,0,0,0,0,0,'point'),
 'DF17':(11,40,0,0,0,0,0,0,'glider'),
 'PHL122':(5,21,0,0,0,25,44,14,'point'),
 'PHL300':(8,30,0,0,0,25,52,21,'point'),
 'PHL370':(10,32,0,0,0,25,58,26,'point'),
 'SR5220':(8,28,0,0,0,26,53,20,'point'),
 'LS6':(15,31,105,149,43,25,64,30,'round'),
}

def missile(key):
 r,n,w0,w1,span,t0,t1,tspan,nose=MISSILES[key];tip=232;front=tip-n;y=80
 s=rect(24,y-r,front-24,2*r)
 if nose=='round':s+=path(f'M{front} {y-r}Q{tip} {y-r} {tip} {y}Q{tip} {y+r} {front} {y+r}Z')
 elif nose=='glider':s+=poly([(front-14,y-r),(tip,y),(front-14,y+r),(front-5,y+23),(front-37,y+r),(front-37,y-r),(front-5,y-23)])
 else:s+=path(f'M{front} {y-r}Q{tip-13} {y-r+1} {tip} {y}Q{tip-13} {y+r-1} {front} {y+r}Z')
 for lo,hi,h in [(w0,w1,span),(t0,t1,tspan)]:
  if not h:continue
  for sign in [-1,1]:s+=poly([(lo,y+sign*r),(lo-4,y+sign*h),(hi-8,y+sign*h),(hi+9,y+sign*r)])
 # Long-chord strakes, not a second set of large forward canards.
 if key=='PL10':s+=poly([(65,73),(76,66),(166,66),(178,73)])+poly([(65,87),(76,94),(166,94),(178,87)])
 if key=='YJ91':
  s+=path('M65 67L86 58H180L192 69H65ZM65 93L86 102H180L192 91H65Z')
 if key in ('KD20','YJ18'):s+=path('M53 92H90L99 104H51Z')
 if key=='LS6':s+=rect(77,58,72,5)
 return s

def tank_gun(length=166,thick=9,sleeve=65,brake=False):
 x=56;end=x+length
 s=path('M22 62H49L67 71V93L49 100H22Z')+rect(x,76,length,thick)+rect(73,72,sleeve,thick+8)
 s+=rect(139,73,11,thick+6)
 if brake:s+=path(f'M{end-8} 72H{end+8}V91H{end-8}Z')
 return s

def auto_gun(barrels=1,rotary=False,chin=False):
 s=path('M26 65H78L94 72H111V99H78L65 93H26Z')
 if chin:s+=path('M43 58H80V43H97V69H43Z')+rect(43,101,49,10)
 if rotary:
  for y in [69,79,89]:s+=rect(99,y,126,5)
  s+=rect(123,65,10,34)+rect(193,65,10,34)+path('M219 65H234V98H219Z')
 else:
  for i in range(barrels):
   y=73+i*11;s+=rect(101,y,123,6)+rect(176,y-2,18,10)+rect(221,y-3,12,12)
 return s

def howitzer(caliber):
 length={122:144,152:160,155:175}[caliber];end=52+length
 return path('M20 74H48L70 61H93V100H45L20 111Z')+rect(53,75,length,10)+rect(61,89,85,8)+rect(end-8,69,18,23)+rect(111,71,15,17)

def hmg(family,mounted=False):
 if family=='QJZ89':
  s=path('M20 70L63 76H82V65H130V73H157V79H231V88H149V99H105L100 118H86L88 99H62L20 111Z')+rect(167,72,40,5)
 elif family=='QJC88':
  s=path('M22 74H62V65H128V73H150V79H230V86H150V95H66L61 112H48V96H22Z')+rect(148,72,43,5)+rect(104,97,24,19)
 elif family=='TYPE86':
  s=path('M18 76H61L75 67H131V74H160V79H233V85H149V95H91L86 116H73L75 96H54L18 108Z')+rect(109,95,30,28)
 elif family=='QJY201':
  s=path('M19 70L65 73L76 64H136V70H162V77H233V84H158V94H108L103 121H87L91 94H66L20 109Z')+path('M86 63V55H134V61H92V65Z')+rect(111,95,30,28)+path('M170 86L154 130H160L177 91L194 130H200L184 86Z')
 elif family=='QJZ171':
  s=path('M18 68H58L72 61H127V72H158V78H231V88H151V99H104L100 120H85L88 98H61L18 106Z')+rect(106,100,30,24)+path('M158 89L143 127H151L166 96L186 127H194L175 89Z')
 elif family=='KPVT':
  s=path('M19 66H118V73H150V79H233V90H150V96H75L65 112H45L48 95H19Z')+rect(131,71,52,6)+rect(101,96,25,24)
 else:raise KeyError(family)
 if mounted:s+=path('M117 99H126V112H151V123H90V112H117Z')
 if family=='QJY201':s=holes(s,'M28 80L59 80L48 94L28 101Z','QJY201')
 return s

def rifle(family):
 if family in ('QBZ95','QBB95','QBU88','QCQ05','QCW05'):
  s=path('M20 70H83L91 64H151V72H171V79H233V85H168V94H141L136 113H122L122 95H88L83 121H65L69 95H20Z')
  s+=path('M49 68V50H118L128 58V65H117V59H60V69Z')
  s+=path('M104 97H119L126 130H106Z')
  if family=='QBU88':s+=rect(94,39,43,10)+rect(107,49,8,11)+path('M167 85L153 130H160L174 94L191 130H198L181 85Z')
  if family=='QBB95':s+=circle(75,117,20)+path('M172 85L159 128H165L177 95L194 128H200L184 85Z')
  if family in ('QCQ05','QCW05'):
   s=path('M23 66H143V73H170V80H203V88H148V99H121L118 122H103V98H82L78 127H61L65 98H23Z')+path('M50 65V47H119V57H62V65Z')
   if family=='QCW05':s+=rect(191,76,45,18)
 elif family in ('QBZ191','QBZ192','QBU191','QJB201','QJS161'):
  short=family=='QBZ192';end=215 if short else 236
  s=path('M19 68L63 69L72 64H126V69H180V84H127L119 94H94L89 116H75L78 93H60L22 110Z')
  s+=rect(180,75,end-180,6)+rect(end-5,72,10,12)+path('M103 94H119L126 123L141 137H124L111 128Z')
  # Open stock, trigger guard, optical rail and front/back iron sights.
  s+=rect(77,60,106,4)+rect(174,54,4,7)+rect(76,54,4,7)
  if family=='QBU191':s+=rect(91,44,53,10)+rect(104,54,8,7)+path('M174 85L159 131H165L179 94L195 131H202L187 85Z')
  if family in ('QJB201','QJS161'):s+=path('M103 96H133L140 126H108Z')+path('M181 84L169 127H175L187 93L202 127H208L194 84Z')
  s=holes(s,'M29 77L57 77L47 90L29 100Z',family)
 elif family=='QTS11':
  s=path('M22 67H99L109 61H174V70H234V79H174V99H142L137 120H121L124 99H91L86 124H69L73 99H22Z')+rect(105,81,132,13)+rect(105,43,51,12)+rect(118,55,8,7)
 elif family=='QBU10':
  s=path('M17 76L66 70H111V64H147V74H235V84H145V97H105L100 121H85L88 96H57L17 112Z')+rect(94,44,60,13)+rect(106,57,8,9)+rect(126,96,29,25)+path('M171 85L151 135H159L178 94L202 135H210L187 85Z')+rect(220,70,17,17)
 elif family=='QBS09':s=path('M20 76L66 71H107V68H233V77H128V86H229V94H116L104 119H87L94 95H62L20 113Z')+rect(139,80,52,12)
 else:raise KeyError(family)
 return s

def launcher(key):
 if key=='HJ73':
  # Exposed missile on an open rail; this is not a tube-launched ATGM.
  return '<g transform="translate(12 -7) scale(.9)">'+missile('HJ73')+'</g>'+rect(51,104,155,5)+rect(97,111,31,16)+path('M107 125L80 147H90L118 132L149 147H159L128 124Z')+rect(50,113,29,18)
 if key=='QN202':
  return path('M24 75H62L74 64H159V73H229V91H153V99H113L106 126H87L91 99H60L24 114Z')+rect(87,43,73,17)+rect(104,60,9,7)+rect(212,68,20,28)
 if key=='TL4':
  return rect(26,54,205,38)+rect(94,98,57,26)+rect(111,91,17,10)+path('M112 123L83 145H95L124 130L156 145H168L134 123Z')+rect(24,50,13,46)+rect(221,50,13,46)
 if key=='FHJ02':
  s=rect(28,50,159,58)+rect(52,44,9,70)+rect(162,44,9,70)
  for x,y in [(216,63),(201,71),(231,71),(216,80),(201,89),(231,89),(216,97)]:
   s+=f'<circle cx="{x}" cy="{y}" r="8" fill="none" stroke="#fff" stroke-width="3"/>'
  s+=path('M100 110H119L151 140H141L112 121L88 140H78Z');return s
 if key in ('QLU11','LG5','LG5S'):
  s=path('M19 74H68L88 62H142V72H230V84H149V103H111L105 124H88L91 102H63L20 117Z')+rect(100,43,59,13)+rect(114,56,8,8)+path('M161 86L147 135H155L168 95L193 135H201L177 86Z')+rect(217,68,20,20)
  if key!='LG5S':s+=circle(128,107,21)
  if key=='LG5':s+=path('M112 123L93 143H103L123 127L149 143H159L133 122Z')
  return s
 if key in ('QLZ87','QLZ04','LG3'):
  s=path('M28 64H129V75H232V87H141V105H70L57 119H40L46 103H28Z')+rect(123,94,16,36)+path('M111 128L88 146H99L126 133L156 146H166L139 127Z')
  s+=circle(87,110,23) if key=='QLZ87' else rect(75,98,49,30)
  if key=='LG3':s+=rect(137,70,66,20)
  return s
 if key in ('LG4','LG6'):
  s=path('M21 77L69 68H129V75H230V87H143V99H111L102 127H84L89 100H63L21 118Z')+circle(135,98,26)
  if key=='LG6':s+=rect(94,49,49,12)+rect(103,61,8,9)
  return s
 if key=='QLG10':return path('M34 68H235V91H120L115 117H98L98 93H34Z')+rect(72,62,95,6)
 if key in ('HJ12','HJ8','HJ73','TL4','GAM102','QN202','MANPADS','PF98','PF89','PF97','DZJ08'):
  wide=key in ('HJ12','PF98','GAM102');y=61;h=27 if wide else 20
  s=rect(29,y,196,h)+rect(22,y-4,11,h+8)+rect(220,y-3,12,h+6)
  if key in ('HJ12','MANPADS','QN202'):s+=rect(115,y+h,38,24)+path(f'M151 {y+h+12}H165V126H151Z')+rect(125,y-16,43,12)
  elif key in ('HJ8','HJ73','TL4','GAM102','PF98'):
   s+=rect(102,y+h,37,29)+rect(90,39,42,17)+path('M115 114L83 142H94L123 121L158 142H169L132 112Z')
  else:s+=path(f'M90 {y+h}H107V112H95Z')+rect(144,y-13,28,11)
  if key=='PF98':s+=rect(187,53,20,43)
  if key=='DZJ08':s+=rect(62,57,86,28)
  return s
 raise KeyError(key)

def pod(diameter):
 # Side profile with visible tube-mouth end; 57-mm pod is longer and slimmer.
 r=25 if diameter==90 else 20
 s=path(f'M30 {80-r}H185L223 68V92L185 {80+r}H30Z')+rect(96,80-r-12,32,12)
 for y in [68,80,92]:s+=circle(217,y,4)
 return s

def get_profile(name,kind):
 n=name.upper()
 if n=='QLU-11':return 'QLU11',launcher('QLU11')
 if n=='QTS-11 GRENADE LAUNCHER':return 'QTS11',rifle('QTS11')
 if n=='HJ-10 AIR-LAUNCHED ATGM':return 'AKD10',missile('AKD10')
 missiles=[('PL-17','PL17'),('PL-15','PL15'),('PL-12','PL12'),('PL-10','PL10'),('PL-8','PL8'),('PL-2','PL2'),('R-73','R73'),('HJ-10','HJ10'),('HJ-73','HJ73'),('HJ-8','HJ8'),('HJ-9','HJ9'),('AKD-10','AKD10'),('BA-7','BA7'),('QN-502','QN502'),('QN-201','QN201'),('HQ-17','HQ17'),('HQ-16','HQ16'),('HQ-12','HQ12'),('HQ-11','HQ11'),('HQ-9','HQ9'),('HQ-7','HQ7'),('HQ-6','HQ6'),('FB-10','FB10'),('FK-2000','FK2000'),('QW-2','QW2'),('TY-90','TY90'),('YJ-91','YJ91'),('YJ-18','YJ18'),('KD-20','KD20'),('KD-88','KD88'),('KH-29','KH29'),('DF-17','DF17'),('DF-15','DF15'),('DF-21','DF21'),('DF-31','DF31'),('SY-400','SY400'),('LS-6','LS6')]
 # Infantry equipment is shown as the launcher, vehicle missiles as the projectile.
 infantry={'HJ-12':'HJ12','HJ-12E':'HJ12','HJ-8E':'HJ8','HJ-73D':'HJ73','TL-4':'TL4','GAM-102LR':'GAM102','QN-202':'QN202','HN-6':'MANPADS','QW-2':'MANPADS','PF-98':'PF98','PF-98A':'PF98','PF-89':'PF89','PF-97':'PF97','DZJ-08':'DZJ08','FHJ-02':'FHJ02','QLU-11':'QLU11','LG5':'LG5','LG5S':'LG5S','LG6':'LG6','LG4':'LG4','LG3':'LG3','QLZ-87':'QLZ87','QLZ-04':'QLZ04','QLG-10A':'QLG10','QTS-11 GRENADE LAUNCHER':'QLG10'}
 if kind=='INFANTRY' and n in infantry:return 'LAUNCHER_'+infantry[n],launcher(infantry[n])
 rifles={'QBZ-191':'QBZ191','QBZ-192':'QBZ192','QBZ-95':'QBZ95','QBZ-97':'QBZ95','QBB-95':'QBB95','QBU-88':'QBU88','QBU-191':'QBU191','QBU-10':'QBU10','QBS-09':'QBS09','QCQ-05':'QCQ05','QCW-05':'QCW05','QJB-201':'QJB201','QJS-161':'QJS161','QTS-11':'QTS11'}
 if n in rifles:return rifles[n],rifle(rifles[n])
 if 'QJZ-171' in n:return 'QJZ171',hmg('QJZ171')
 if 'QJZ-89' in n:return 'QJZ89'+('_MOUNT' if kind!='INFANTRY' else ''),hmg('QJZ89',kind!='INFANTRY')
 if 'QJC-88' in n:return 'QJC88',hmg('QJC88',True)
 if 'QJY-201' in n:return 'QJY201',hmg('QJY201')
 if 'TYPE 86' in n or '7.62 MM CABIN' in n:return 'TYPE86',hmg('TYPE86')
 if '14.5' in n:return 'KPVT',hmg('KPVT',True)
 if n.startswith('100 MM GUN /'):return 'GUN100_BMP',tank_gun(145,10,40)
 for match,key in missiles:
  if match in n:return key,missile(key)
 if n.startswith('PHL-'):key='PHL370' if '370' in n else 'PHL300' if '300' in n else 'PHL122';return key,missile(key)
 if n.startswith('SR-5'):return 'SR5220',missile('SR5220')
 if 'UNGUIDED ROCKETS' in n:d=57 if '57' in n else 90;return 'POD'+str(d),pod(d)
 if 'HOWITZER' in n:c=122 if '122' in n else 152 if '152' in n else 155;return 'HOWITZER'+str(c),howitzer(c)
 if 'GUN-MORTAR' in n:return 'GUN_MORTAR120',tank_gun(120,12,40,True)
 if '125 MM' in n or 'ZPT-98' in n:return 'ZPT98',tank_gun(178,9,71)
 if '120 MM' in n:return 'TANK120',tank_gun(170,10,68)
 if '105 MM' in n:return 'TANK105',tank_gun(161,8,55,True)
 if '100 MM' in n:return ('GUN100_BMP',tank_gun(145,10,40)) if 'LAUNCHER' in n else ('GUN100_RIFLED',tank_gun(158,8,49))
 if '85 MM' in n:return 'GUN85',tank_gun(148,7,40)
 if '73 MM' in n:return 'GUN73',tank_gun(112,12,29)
 if '625' in n:return 'ROTARY25',auto_gun(rotary=True)
 if 'TWIN 35' in n or 'PG99' in n:return 'TWIN35',auto_gun(barrels=2)
 if 'FOUR 25' in n:return 'QUAD25',auto_gun(barrels=4)
 if 'TWIN 30' in n:return 'TWIN30',auto_gun(barrels=2,chin=True)
 if 'TWIN 37' in n:return 'TWIN37',auto_gun(barrels=2)
 if '76 MM' in n:return 'NAVAL76',path('M24 109L35 67L72 48H114L142 76L234 61L237 70L151 91L148 112Z')
 if 'CHIN CANNON' in n:return ('CHIN23' if '23' in n else 'CHIN30'),auto_gun(barrels=2 if '23' in n else 1,chin=True)
 if '23' in n:return 'GSH23',auto_gun(barrels=2)
 if '30' in n:return ('ZPT99' if 'ZPT-99' in n or 'AUTOCANNON' in n else 'GSH301'),auto_gun()
 if 'LOITERING' in n:return 'LOITERING_PROXY',rect(34,74,180,12)+poly([(123,74),(83,28),(103,28),(157,74)])+poly([(123,86),(83,132),(103,132),(157,86)])
 if n=='UAV GUIDED MISSILE':return 'UNSPECIFIED_UAV_ATGM',missile('BA7')
 raise ValueError((name,kind,'No reviewed weapon family mapping'))

def svg(shape):
 return '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="160" viewBox="0 0 256 160"><g fill="#fff">'+shape+'</g></svg>\n'
