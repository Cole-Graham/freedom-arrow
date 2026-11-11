"""Editable photo-referenced bullpup contours. Related-family variants are marked approximations."""
from pathlib import Path
import json
out=Path(__file__).resolve().parent/'hud-reference-vectors';out.mkdir(exist_ok=True)
# Coordinates follow the source side views, muzzle right; final vector transform faces left.
body='M4 22 Q3 18 7 18 L22 18 Q26 17 30 20 L76 20 L80 8 Q81 4 86 4 L128 5 Q133 5 135 10 L142 20 L165 20 L168 11 L170 11 L170 6 Q171 4 174 5 L176 7 L176 21 L179 25 L178 35 Q176 38 170 38 L145 38 L142 48 Q141 52 137 51 L130 48 L128 43 L112 43 L110 61 Q110 64 106 63 L97 61 Q95 60 97 56 L101 40 L83 42 L38 42 L28 44 L20 52 L7 52 Q4 52 4 48 Z'
handle='M85 10 Q86 9 89 9 L126 10 Q128 10 130 13 L133 20 L86 20 Z'
trigger='M113 39 L132 38 L130 44 Q128 47 124 45 L114 42 Z'
mag95='M51 42 L70 42 Q72 62 84 75 L76 84 Q58 69 51 42 Z'
mag97='M51 42 L67 42 L72 70 L56 72 Z'
barrel='M177 27 L201 27 L202 25 L211 25 L214 27 L214 31 L211 33 L202 33 L201 31 L178 32 Z'
vents='M145 23h3v1.3h-3z M150 23h3v1.3h-3z M155 23h3v1.3h-3z M160 23h3v1.3h-3z M165 23h3v1.3h-3z'
# Long barrel and support bipod distinguish the QBB family; a family approximation, not an exact owned mesh.
qbbbarrel='M177 27 L218 27 L219 25 L229 25 L231 27 L231 31 L229 33 L219 33 L218 31 L178 32Z M207 31 L211 31 L223 64 L220 66 L208 37 L197 65 L194 64Z'
drum='M48 42 L72 42 L75 50 C87 52 88 74 73 79 C57 84 45 68 50 55 Z'
qbu='M3 27 Q3 24 6 24 L53 24 L55 21 L66 21 L68 19 L78 19 L79 22 L94 22 L94 24 L136 24 L138 20 L148 20 L152 23 L158 23 L159 28 L160 32 L198 32 L200 30 L216 30 Q218 31 218 34 L217 36 L199 36 L198 35 L160 35 L158 38 L151 39 L149 43 L143 44 L96 44 L94 50 Q94 55 89 55 L79 55 L77 68 Q78 70 74 70 L65 68 Q63 67 65 63 L70 49 Q72 44 67 43 L54 43 L53 63 L38 64 L38 52 L18 52 L13 61 L5 61 Q3 61 3 57 Z'
qbuscope='M49 4 L52 4 L53 7 L65 8 L67 10 L82 10 L83 7 L87 7 L87 3 L92 3 L92 7 L95 7 L97 9 L112 6 L116 6 L117 14 L112 15 L96 14 L96 19 L94 20 L80 20 L80 14 L67 14 L65 16 L53 15 L52 18 L49 18 Q46 12 49 4 Z M82 20 L93 20 L93 24 L82 24 Z'
qbubipod='M162 36 L165 36 L165 42 L217 42 L218 39 L224 38 L226 43 L225 47 L219 46 L166 46 Q162 45 162 41Z'
qbutrigger='M82 44 L93 44 L91 50 Q90 53 86 52 L81 51 Z'
profiles={'QBZ95':(218,88,body+mag95+barrel+handle+trigger+vents,'QBZ95 photo contour'),'QBZ97':(218,77,body+mag97+barrel+handle+trigger+vents,'QBZ95 family approximation with straight magazine'),'QBB95':(235,88,body+drum+qbbbarrel+handle+trigger+vents,'QBZ95 support-weapon family approximation with drum, barrel and bipod'),'QBU88':(230,74,qbu+qbuscope+qbubipod+qbutrigger,'QBU88 photo contour')}
receipt=[]
for name,(w,h,d,basis) in profiles.items():
 for outline in (False,True):
  suffix='_OUTLINE' if outline else '';style='fill="#435047" stroke="#e7f7e4" stroke-width="0.85" stroke-linejoin="round"' if outline else 'fill="#e7f7e4"'
  # Scale the vector canvas only, preserving aspect; transparent edge margin included in paths.
  scale=232/w;height=round(h*scale,3)
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="232" height="{height}" viewBox="0 0 {w} {h}"><g transform="translate({w} 0) scale(-1 1)"><path {style} fill-rule="evenodd" d="{d}"/></g></svg>\n'
  (out/('FA_PLA_WP_'+name+suffix+'.svg')).write_text(svg)
 receipt.append({'profile':name,'basis':basis,'source':'https://commons.wikimedia.org/wiki/File:Qbu-88-0.jpg' if name=='QBU88' else 'https://commons.wikimedia.org/wiki/File:QBZ95_automatic_rifle_mod_noBG.png','method':'Original editable contour vector; no photo pixels copied'})
(out/'reference-contours.json').write_text(json.dumps(receipt,indent=2)+'\n')
