"""Render code-native white silhouettes for PLA weapon/ammunition HUD addresses."""
from pathlib import Path
import json,subprocess,argparse
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'releases/0.6';out=R/'source/runtime-qa/icons'
p=argparse.ArgumentParser();p.add_argument('--renderer',required=True);a=p.parse_args()
shapes={
 'CANNON':'<path d="M24 75h48l16-20h45l15 12h89v12H138l-13 15H75l-14 16H24z"/><path d="M91 95h10v27H88z"/>',
 'AUTOCANNON':'<path d="M27 78h68l15-17h46v10h82v6h-82v8h82v6h-82v9h-46L95 90H27z"/><path d="M98 96h23v25H93z"/>',
 'MG':'<path d="M16 74h56l19-13h63v10h80v9h-80v13h-49l-6 25H83l5-25H56l-40 12z"/><path d="M131 91l20 38h7l-12-38z"/>',
 'ATGM':'<rect x="32" y="52" width="178" height="30" rx="4"/><path d="M109 82h13v17l-30 35h-10l25-39-25 39h-9l32-47zM124 94l33 40h-11l-29-34z"/><rect x="86" y="36" width="25" height="15"/>',
 'SAM':'<path d="M28 79l33-22h126l39 22-39 22H61z"/><path d="M73 59l-18-28h24l29 28zM73 99l-18 28h24l29-28zM163 60l-10-23h20l18 23zM163 98l-10 23h20l18-23z"/>',
 'MISSILE':'<path d="M29 80l38-15h128l35 15-35 15H67z"/><path d="M68 64L46 31h28l34 33zM68 96l-22 33h28l34-33zM163 65l-18-22h23l20 22zM163 95l-18 22h23l20-22z"/>',
 'ROCKET':'<rect x="27" y="48" width="177" height="17" rx="5"/><rect x="27" y="72" width="177" height="17" rx="5"/><rect x="27" y="96" width="177" height="17" rx="5"/><path d="M202 48l29 8-29 9zM202 72l29 8-29 9zM202 96l29 8-29 9z"/>',
 'HOWITZER':'<path d="M31 108h81l31-20h39v19h30v12H31zM104 92l16-20 96-42 6 14-93 44z"/><circle cx="80" cy="126" r="13"/><circle cx="174" cy="126" r="13"/>',
 'MORTAR':'<path d="M75 29l18-7 43 92-18 9zM116 119h29v11H93v-8zM107 88h19l37 48h-12l-29-35-11 35h-12z"/>',
 'BOMB':'<path d="M54 80l35-21h83l44 21-44 21H89zM70 60L34 32h29l39 28zM70 100l-36 28h29l39-28z"/>',
 'RIFLE':'<path d="M19 78h43l19-12h64v7h89v8h-89v13h-38l-7 26H85l4-26H58l-39 15z"/>',
 'SNIPER':'<path d="M17 82h44l25-12h57v7h94v6h-94v12h-38l-6 20H84l4-20H57l-40 12z"/><rect x="89" y="50" width="64" height="12" rx="3"/><path d="M100 62h8v9h-8zM135 62h8v9h-8zM151 88l12 38h7l-7-38z"/>',
 'GRENADE':'<path d="M28 71h142l26 10v20h-82l-4 26H91l4-26H64l-36 17z"/><circle cx="134" cy="88" r="22"/><rect x="163" y="73" width="64" height="12"/>',
 'SHOTGUN':'<path d="M18 86h52l25-15h140v8H128v12h-20l-11 23H81l5-22H60l-42 20z"/><rect x="138" y="85" width="62" height="9"/>',
 'SMG':'<path d="M25 74h132v10h63v8h-63v13h-30l-6 28h-19l3-28H79l-9 24H52l8-24H25z"/><path d="M27 76L9 65v39l18-8z"/>'}
keys=set()
for n in ['pla-vehicle-armament.json','pla-infantry-designer.json']:keys.update(json.loads((R/'source/UserData/FreedomArrow'/n).read_text())['icon_keys'])
for key in sorted(keys):
 kind=key.split('_')[-1];shape=shapes[kind]
 if '_AMMO_' in key:
  if kind in ['RIFLE','MG','AUTOCANNON','CANNON','SNIPER','SMG','SHOTGUN']:
   shape=''.join(f'<path d="M{x} 129V56l12-28 12 28v73z"/><rect x="{x-2}" y="130" width="28" height="7"/>' for x in [62,116,170])
  elif kind=='GRENADE':shape='<path d="M86 57h84v59H86z"/><rect x="102" y="38" width="48" height="19" rx="4"/><path d="M149 39l28 10 7 48h-9l-10-38-21-8z"/>'
  else:shape='<g transform="translate(8 0)">'+shape+'</g>'
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="256" height="160" viewBox="0 0 256 160"><g fill="#fff">'+shape+'</g></svg>'
 (out/(key+'.svg')).write_text(svg)
 subprocess.run([a.renderer,'-o',str(out/(key+'.png')),str(out/(key+'.svg'))],check=True)
print('Rendered',len(keys),'transparent HUD icons')
