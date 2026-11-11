"""Editable vector details and real transparent overlap gaps for Build21 insignia.
These are game adaptations of documented motifs, not exact issued-patch reproductions.
"""
IVORY='#e7f7e4'
_serial=0
def path(d,fill=IVORY,**kw):
 return '<path d="'+d+'" fill="'+fill+'" '+' '.join(k.replace('_','-')+'="'+str(v)+'"' for k,v in kw.items())+'/>'
def stroke(d,w=2.2):return path(d,'none',stroke=IVORY,stroke_width=w,stroke_linejoin='round',stroke_linecap='round')
def cut(body,holes):
 global _serial
 _serial+=1;key='cut'+str(_serial)
 return f'<defs><mask id="{key}" maskUnits="userSpaceOnUse" x="0" y="0" width="256" height="160"><rect width="256" height="160" fill="white"/>'+f'<g fill="black" stroke="black">{holes}</g></mask></defs><g mask="url(#{key})">{body}</g>'
def overlap(back,front,gap=3.2):
 # Dilate the foreground silhouette in the background's mask. The gap is real alpha,
 # so it keeps working against every native panel colour instead of painting a dark stripe.
 holes=f'<g stroke="black" stroke-width="{gap*2}" stroke-linejoin="round" stroke-linecap="round">{front.replace(IVORY,"black")}</g>'
 return cut(back,holes)+front
def star(x,y,r):
 import math
 return path('M'+'L'.join(f'{x+math.sin(i*math.pi/5)*(r if i%2==0 else r*.42):.2f},{y-math.cos(i*math.pi/5)*(r if i%2==0 else r*.42):.2f}' for i in range(10))+'Z')
def sword():
 blade=path('M128 10 Q132 22 133 32 L132 96 L143 102 Q148 104 147 108 L132 106 L132 115 L134 119 L132 124 L124 124 L122 119 L124 115 L124 106 L109 108 Q108 104 113 102 L124 96 L123 32 Q124 22 128 10Z')
 return cut(blade,path('M127 31 L129 26 L129 96 L127 96Z','black')+path('M125 112 L131 112 M125 117 L131 117','none',stroke='black',stroke_width=1.4))
def wolf(cat=False):
 if not cat:
  outer='M128 43 C119 42 114 46 109 48 Q103 39 98 26 Q89 36 90 54 Q85 64 89 77 L86 86 L95 84 Q92 94 98 100 L98 108 L108 107 Q111 119 128 130 Q145 119 148 107 L158 108 L158 100 Q164 94 161 84 L170 86 L167 77 Q171 64 166 54 Q167 36 158 26 Q153 39 147 48 C142 46 137 42 128 43Z'
  holes='M97 38 Q101 48 103 54 L95 58 Q92 49 97 38Z M159 38 Q155 48 153 54 L161 58 Q164 49 159 38Z M97 63 Q109 59 120 69 Q110 67 101 70Z M159 63 Q147 59 136 69 Q146 67 155 70Z M101 73 Q111 72 118 77 Q112 82 103 79Z M155 73 Q145 72 138 77 Q144 82 153 79Z M121 87 Q128 83 135 87 L132 94 L124 94Z M111 99 Q128 106 145 99 Q142 114 133 119 L123 119 Q114 114 111 99Z M103 84 Q110 86 115 91 L107 89Z M153 84 Q146 86 141 91 L149 89Z'
 else:
  outer='M128 43 Q115 42 108 47 C102 36 90 34 88 46 Q85 55 92 61 Q86 71 91 86 Q92 101 104 112 Q114 123 128 127 Q142 123 152 112 Q164 101 165 86 Q170 71 164 61 Q171 55 168 46 C166 34 154 36 148 47 Q141 42 128 43Z'
  holes='M97 45 Q105 43 104 54 L96 56 Q92 49 97 45Z M159 45 Q151 43 152 54 L160 56 Q164 49 159 45Z M99 69 Q109 63 120 72 L115 77 Q106 71 99 74Z M157 69 Q147 63 136 72 L141 77 Q150 71 157 74Z M119 85 Q128 81 137 85 L132 94 L124 94Z M109 97 Q128 104 147 97 Q145 113 134 119 L122 119 Q111 113 109 97Z'
 body=cut(path(outer),path(holes,'black'))
 # Teeth and muzzle remain pale inside the transparent mouth; tapered cheek marks read at small size.
 body+=path('M116 101 L122 103 L121 111 Q118 108 116 101Z M134 103 L140 101 Q138 108 135 111Z M122 116 L126 112 L126 119Z M130 112 L134 116 L130 119Z')
 if cat:
  spots='M111 53 Q115 49 118 54 Q117 59 112 57Z M138 54 Q141 49 145 53 L144 57 L139 58Z M101 86 Q105 82 108 86 L106 90 L102 90Z M148 86 Q151 82 155 86 L154 90 L150 90Z M110 92 L114 90 L117 93 L115 96 L111 95Z M139 93 L142 90 L146 92 L145 95 L141 96Z'
  body=cut(body,path(spots,'black'))
 else:
  body=cut(body,path('M118 52 Q121 57 124 61 L120 60Z M138 52 L136 60 L132 61 Q135 57 138 52Z M97 92 L104 96 L102 99Z M159 92 L154 99 L152 96Z','black'))
 return body

def dragon():
 # Open S-shaped body, curved horns, distinct jaw, belly/scales and four-finger claws.
 body=stroke('M147 49 C169 59 158 80 136 77 C106 71 94 81 100 98 C106 116 138 119 148 102 C158 85 141 81 131 91 C124 99 137 105 143 99',11)
 head=path('M142 48 Q134 43 135 37 Q141 36 146 42 Q145 29 150 26 L153 39 Q159 29 164 31 L159 43 Q168 41 173 46 L164 50 L174 56 Q169 64 158 60 L153 68 Q146 66 141 58 L132 60 Q128 55 134 51Z')
 limbs=path('M112 80 Q104 70 96 68 L94 72 L100 78 L91 77 L89 81 L101 85 L94 88 L97 92 L109 88Z M144 111 L155 119 L159 115 L154 109 L163 110 L165 106 L153 103 L159 99 L156 96 L145 103Z')
 detail=path('M156 46 Q160 44 164 47 L160 50 L156 49Z M157 55 L165 55 L162 58 L157 58Z','black')
 # Belly/scales use broad cutouts rather than dense black engraving.
 detail+=path('M108 87 Q106 93 111 97 M117 101 L120 108 M128 104 L131 111 M139 101 L145 105 M147 68 L151 73','none',stroke='black',stroke_width=2,stroke_linecap='round')
 whiskers=stroke('M166 57 Q179 62 174 72 M157 62 Q166 72 160 80',1.8)
 return cut(body+head+limbs,detail)+whiskers

def shield(contents,round=False):
 if round:
  border='<circle cx="128" cy="80" r="66" fill="none" stroke="'+IVORY+'" stroke-width="3.5"/><circle cx="128" cy="80" r="60" fill="none" stroke="'+IVORY+'" stroke-width="1.4"/>'
 else:border=stroke('M77 25 Q128 8 179 25 L175 91 Q165 124 128 146 Q91 124 81 91Z',3.4)+stroke('M84 30 Q128 16 172 30 L168 89 Q159 117 128 137 Q97 117 88 89Z',1.3)
 return border+contents

def overrides(base,anchor,wings,canopy):
 sw=sword();wing=wings(51)
 thunder=overlap(wing,canopy(35),2.5)
 thunder=overlap(thunder,sw,2.5)+path('M92 72 L107 89 L100 88 L113 113 L91 94 L98 93 L84 76Z M164 72 L149 89 L156 88 L143 113 L165 94 L158 93 L172 76Z')
 # The Godsword blade clears the map by3px on each side, including the quillons.
 china=path('M94 61 Q99 56 109 58 L114 49 L126 47 L135 53 L143 41 L151 46 L157 41 L165 53 L155 64 L157 76 L146 84 L142 97 L128 99 L120 111 L111 103 L104 88 L94 85 L88 73Z')
 god=overlap(china,sw,3.4)
 sea=overlap('<g transform="translate(-7 6)">'+anchor()+'</g>','<g transform="translate(48 9) scale(.74)">'+dragon()+'</g>',3.2)
 # Crossbow detail with separated shaft, bolt and helmet layers.
 helm=cut(path('M104 83 Q104 60 128 58 Q152 60 152 83 L146 86 L146 96 L110 96 L110 86Z'),path('M111 83 L145 83 L145 88 L111 88Z','black'))
 bow=stroke('M86 59 Q128 29 170 59 M91 60 L128 111 L165 60',3.1)
 arrow=path('M128 14 L133 29 L130 27 L130 121 L134 128 L128 125 L122 128 L126 121 L126 27 L123 29Z')
 xiang=overlap(helm+bow,arrow,2.2)
 # Preserve the police/PAP forms while making their interior objects distinct.
 police=base['POLICE'];pap=base['PAP']
 # Generic sword/bolt remains an explicitly generic fallback, with a real gap at crossing.
 bolt=path('M147 41 L111 75 L127 75 L110 103 L153 67 L135 67Z')
 sof=overlap(sw,bolt,2.2)
 rocket_sof=overlap(path('M100 70 L114 83 L108 82 L118 106 L97 90 L103 90 L91 74Z M156 70 L142 83 L148 82 L138 106 L159 90 L153 90 L165 74Z'),sw,2.2)
 # Corps-level real patch motifs are used where no brigade-specific patch was verified.
 airborne=shield(star(128,41,17)+'<g transform="translate(25 36) scale(.80)">'+overlap(wings(77),canopy(53),2.3)+star(128,101,10)+'</g>')
 marine=shield('<g transform="translate(23 20) scale(.82)">'+overlap(anchor(),path('M87 43 L93 42 L153 115 L149 119Z M169 43 L163 42 L103 115 L107 119Z'),2.6)+star(128,9,12)+'</g>',True)
 ground=shield(star(128,51,20)+overlap(path('M94 86 L100 82 L151 119 L146 123Z'),path('M162 86 L156 82 L105 119 L110 123Z'),2.8))
 rocket=shield('<g transform="translate(24 20) scale(.81)">'+base['ROCKET']+'</g>')
 reserve=shield(star(128,52,20)+path('M103 80 L112 80 L128 101 L144 80 L153 80 L132 110 L132 129 L124 129 L124 110Z'))
 # Historic80th Motorized patch: side-facing tiger head with sweeping neck,
 # an open jaw around an upright bear, and a descending arrow. Shape read from photo,
 # not from the search engine's incorrect front-facing-tiger caption.
 tiger=path('M151 34 Q157 43 160 54 L164 88 Q161 110 141 128 L124 143 L108 126 L103 113 Q120 124 137 115 Q145 109 145 101 Q127 105 116 96 L130 91 Q145 82 142 70 Q141 58 126 58 L113 61 L112 56 L104 58 L109 50 L125 45 L134 36 L141 41 L147 32Z')
 tiger=cut(tiger,path('M128 49 Q134 44 138 48 Q138 54 132 55 L128 53Z M115 58 L119 56 L121 59 L118 61Z M151 47 L155 54 M153 59 L157 67 M154 73 L158 81 M152 88 L156 92','none',stroke='black',stroke_width=2.2,stroke_linecap='round'))
 tiger+=path('M100 42 L112 49 Q96 65 101 82 L107 78 L100 96 L91 80 L96 82 Q89 63 100 42Z')
 bear=path('M110 75 Q110 69 115 70 Q117 66 121 70 L125 72 L126 77 L120 79 L119 86 L126 87 L127 92 L119 91 L117 101 L121 107 L117 111 L111 105 L110 96 L105 91 L105 83Z')
 motor=shield(overlap(tiger,bear,2.8))
 # Name-inspired game emblems where exact issued badges remain unverified.
 blood=overlap('<g transform="translate(0 16)">'+sw+'</g>',wolf(),2.2)
 plateau=wolf(True)+stroke('M94 137 L111 119 L121 129 L134 117 L154 137Z',2.7)
 falcon=path('M93 112 Q112 98 112 80 Q100 61 112 47 Q125 33 145 41 L160 53 L171 58 L166 68 L151 70 Q143 87 153 109 L140 125 L121 129Z')
 falcon=cut(falcon,path('M133 51 Q142 47 149 55 L143 58 L136 57Z M154 59 L165 60 L161 64 L151 65Z M117 86 Q126 94 134 96 M116 98 L132 106 M118 109 L130 116','none',stroke='black',stroke_width=2.4,stroke_linecap='round'))
 eagle=overlap(wings(71),path('M124 54 Q127 46 133 49 L141 54 L134 59 L134 76 L143 102 L135 99 L128 113 L121 99 L113 102 L122 76Z'),2.2)+star(128,32,13)
 return {'AIRBORNE':overlap(wings(64),canopy(44)+star(128,86,12),2.2),'GROUND':ground,'MARINE':marine,'ROCKET':rocket,'ROCKET_SOF':rocket_sof,'SOF':sof,'LEISHEN':thunder,'DONGFANG':god,'XIANGJIAN':xiang,'TIANLANG':wolf(),'SNOW_LEOPARD':wolf(True),'JIAOLONG':sea,'POLICE':police,'PAP':pap,'LINE_AIRBORNE':airborne,'LINE_MARINE':marine,'LINE_MOTOR80':motor,'LINE_GROUND':ground,'LINE_RESERVE':reserve,'LINE_ROCKET':rocket,'BLOOD_WOLF':blood,'PLATEAU_LEOPARD':plateau,'FALCON':falcon,'EAGLE':eagle}
