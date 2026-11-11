"""Build22 feedback: fierce faces, clearer birds, coiled dragon and larger shield motifs."""
from detailed_insignia import path,stroke,cut,overlap,shield,IVORY

def fierce_leopard():
 outer=path('M128 43 Q114 40 106 48 Q100 36 91 40 Q84 46 93 61 Q87 76 94 91 Q97 105 110 116 Q119 126 128 129 Q137 126 146 116 Q159 105 162 91 Q169 76 163 61 Q172 46 165 40 Q156 36 150 48 Q142 40 128 43Z')
 holes=path('M96 47 Q101 45 102 53 L96 56 Q92 52 96 47Z M160 47 Q155 45 154 53 L160 56 Q164 52 160 47Z M99 63 Q109 60 121 71 L116 75 Q108 70 100 69Z M157 63 Q147 60 135 71 L140 75 Q148 70 156 69Z M102 74 Q110 73 117 78 L113 82 L104 79Z M154 74 Q146 73 139 78 L143 82 L152 79Z M120 87 Q128 82 136 87 L132 95 L124 95Z M116 99 L124 100 L128 97 L132 100 L140 99 L141 112 L135 123 L121 123 L115 112Z M107 87 L114 91 L111 94 L104 90Z M149 87 L142 91 L145 94 L152 90Z M114 55 L120 58 L119 62 L114 60Z M142 55 L136 58 L137 62 L142 60Z','black')
 holes+=path('M118 80 Q122 77 125 78 M131 78 Q134 77 138 80 M101 96 L110 98 M155 96 L146 98','none',stroke='black',stroke_width=2,stroke_linecap='round')
 face=cut(outer,holes)
 # Long upper canines, squared open snarl and lower incisors: no upturned smile corners.
 face+=path('M119 100 L124 102 L122 114 L119 111Z M132 102 L137 100 L137 111 L134 114Z M122 120 L125 115 L127 121Z M129 121 L131 115 L134 120Z')
 spots=path('M106 53 Q110 49 112 54 L110 58 L106 57Z M146 53 Q150 49 150 54 L150 57 L146 58Z M123 49 L128 47 L133 49 L131 53 L125 53Z M99 84 L103 82 L106 85 L104 88 L100 88Z M157 84 L153 82 L150 85 L152 88 L156 88Z M106 102 L111 103 L112 108 L108 107Z M150 102 L145 103 L144 108 L148 107Z','black')
 return cut(face,spots)

def falcon_head():
 # Compact hooked upper beak and black falcon malar stripe; avoid a flat projecting duck bill.
 outer=path('M95 119 Q105 104 107 91 Q103 81 103 68 C101 48 112 35 131 34 Q145 32 156 45 L161 54 Q175 57 178 68 Q179 78 170 87 L169 76 L160 74 Q157 87 146 94 L147 111 L139 124 L129 132 L120 126 L109 133 L109 123Z')
 cuts=path('M121 53 Q133 45 145 54 L142 59 Q133 54 124 59Z M125 61 L139 59 L137 65 L130 66Z M153 57 Q159 56 163 62 L158 65 L153 62Z M161 68 L171 68 L167 71 L161 71Z M130 70 L140 68 Q136 80 126 90 L120 91 Q128 80 130 70Z M115 94 Q125 97 135 96 L131 100 L117 100Z M113 105 L130 105 L126 110 L114 110Z M116 116 L125 114 L122 120Z','black')
 return cut(outer,cuts)

def eagle():
 # Broad feathered wings with curved overlapping primaries and an upright hooked-beak head.
 wing=path('M119 73 Q100 65 86 51 Q73 38 48 32 Q47 43 59 51 Q41 43 29 45 Q34 58 53 62 Q39 61 32 65 Q41 77 61 78 Q48 80 43 85 Q55 94 74 90 Q64 99 63 104 Q79 107 91 99 Q88 109 92 113 Q107 108 119 92Z')
 cuts=path('M54 44 Q75 52 94 70 M47 56 Q70 64 91 76 M47 70 Q69 74 92 83 M58 85 Q77 83 96 88 M76 98 L101 91','none',stroke='black',stroke_width=2.1,stroke_linecap='round')
 wing=cut(wing,cuts);wings=wing+'<g transform="translate(256 0) scale(-1 1)">'+wing+'</g>'
 body=path('M121 50 Q119 40 126 34 Q137 30 143 40 L147 45 L159 49 Q159 57 151 62 L150 54 L141 56 Q137 63 138 73 L145 91 L148 102 L139 99 L144 109 L134 105 L140 128 L129 121 L128 132 L118 122 L111 129 L116 105 L106 110 L112 99 L103 104 L111 87 Q121 68 121 50Z')
 body=cut(body,path('M128 43 L138 42 L136 47 L130 48Z M142 48 L150 49 L146 52Z M123 61 Q130 66 135 61 M120 77 L127 82 L135 76 M119 87 L127 92 L137 86 M122 101 L128 106 L133 100','none',stroke='black',stroke_width=1.8,stroke_linecap='round'))
 return overlap(wings,body,2.4)

def dragon():
 body=stroke('M151 49 C176 54 165 78 142 73 C114 67 97 79 106 97 C115 116 149 110 151 92 C152 79 135 80 131 90 C129 97 137 102 142 96',8.5)
 head=path('M144 49 Q137 46 136 40 Q141 37 148 42 Q145 31 151 27 L155 41 Q160 31 166 34 L161 45 L172 46 L169 51 L179 55 Q178 64 169 65 L160 62 L153 70 Q145 66 142 58 L133 59 L130 55Z')
 claws=path('M111 80 L101 70 L96 71 L102 80 L94 79 L92 83 L104 87 L98 91 L102 94 L113 88Z M143 109 L154 118 L159 115 L153 109 L161 111 L164 107 L152 102 L159 98 L156 95 L146 101Z')
 detail=path('M155 48 Q160 45 166 49 L162 53 L157 53Z M166 57 L174 57 L171 60 L166 60Z','black')+path('M108 88 L112 91 M116 98 L118 105 M127 102 L130 109 M140 100 L145 105 M151 66 L155 70','none',stroke='black',stroke_width=1.7,stroke_linecap='round')
 whiskers=stroke('M173 62 Q186 67 179 76 M164 65 Q174 77 165 83',1.7)
 return cut(body+head+claws,detail)+whiskers

def strong_sword():
 return cut(path('M128 9 Q136 24 137 36 L136 94 L151 100 Q155 102 153 107 L136 105 L136 113 L139 119 L135 126 L121 126 L117 119 L120 113 L120 105 L103 107 Q101 102 105 100 L120 94 L119 36 Q120 24 128 9Z'),path('M127 42 L129 42 L129 90 L127 90Z M123 113 L133 113 M123 119 L133 119','none',stroke='black',stroke_width=1.5))

def apply(central,anchor,wings,canopy):
 leopard=fierce_leopard()
 china=path('M94 61 Q99 56 109 58 L114 49 L126 47 L135 53 L143 41 L151 46 L157 41 L165 53 L155 64 L157 76 L146 84 L142 97 L128 99 L120 111 L111 103 L104 88 L94 85 L88 73Z')
 central['DONGFANG']=overlap(china,strong_sword(),3.1)
 # The dragon crosses and visibly coils around the shaft again; gap cuts preserve its contour.
 central['JIAOLONG']=overlap('<g transform="translate(-3 4)">'+anchor()+'</g>',dragon(),2.6)
 central['SNOW_LEOPARD']=leopard
 central['PLATEAU_LEOPARD']=leopard+stroke('M94 138 L111 120 L121 130 L134 118 L154 138Z',2.7)
 central['FALCON']=falcon_head();central['EAGLE']=eagle()
 # Stars removed. Large parachute and flight wings occupy the shield's central field.
 wing=path('M121 79 Q98 76 78 60 Q79 73 91 80 L82 79 Q89 90 104 94 L96 96 Q106 106 121 102 L128 91Z')
 wing=cut(wing,path('M84 70 Q101 81 117 85 M91 84 L116 91 M103 96 L120 96','none',stroke='black',stroke_width=1.8,stroke_linecap='round'))
 wing+= '<g transform="translate(256 0) scale(-1 1)">'+wing+'</g>'
 top=path('M95 57 C94 22 162 22 161 57 L152 53 L145 57 L136 53 L128 57 L120 53 L111 57 L104 53Z')
 top=cut(top,path('M128 30 L128 53 M116 32 Q110 40 110 53 M140 32 Q146 40 146 53 M104 39 L101 51 M152 39 L155 51','none',stroke='black',stroke_width=1.7,stroke_linecap='round'))
 cords=stroke('M96 57 L125 120 M111 57 L126 120 M128 57 L128 120 M145 57 L130 120 M160 57 L131 120',2)
 interior='<defs><clipPath id="airborneInterior22"><path d="M87 33 Q128 20 169 33 L165 88 Q156 115 128 133 Q100 115 91 88Z"/></clipPath></defs><g clip-path="url(#airborneInterior22)">'+overlap(wing,top+cords,2.3)+'</g>'
 central['LINE_AIRBORNE']=shield(interior)
 rocket=path('M128 27 Q142 45 143 64 L143 104 L156 126 L140 121 L135 134 L121 134 L116 121 L100 126 L113 104 L113 64 Q114 45 128 27Z')
 rocket=cut(rocket,path('M125 47 L128 39 L131 47 L131 101 L125 101Z M115 68 L141 68 M115 101 L141 101','none',stroke='black',stroke_width=1.8,stroke_linecap='round'))
 central['LINE_ROCKET']=shield('<g transform="translate(12.8 4) scale(.9)">'+rocket+'</g>')
 return central
