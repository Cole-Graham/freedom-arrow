#!/usr/bin/env bash
# AH-1W with its weapon stores kept (Shawn 28 Nov 12:2x "Can also attach the weapons on the original models, do not delete").
set -e
R=/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125; W=/home/sam/tars/work/ba-dev/replicas/codex/work
BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; PY=$W/pla-0.9/armory-opt/.venv/bin/python
cd $R/veh; s=ah1w
UPSIGN=1 timeout 1200 nice -n 10 $BL -b -P ../tools/plane_prep.py -- x/$s/${s}_raw.glb x/$s/$s.glb - '^$' > x/$s/prep.log 2>&1; grep -E "DROPPED|ORIENT" x/$s/prep.log
rm -rf x/$s/pre-glassuv
cd $R/tools; timeout 3000 ./finish_one.sh ah1w 14.9 60000 30000 2>&1 | tail -6
cd $R/veh/models; for l in l1 l2; do cp m_roc_ah1w_lo_static.mat.json m_roc_ah1w_lo_static_$l.mat.json; done
$PY - <<'P'
import json,glob
for f in sorted(glob.glob('m_roc_ah1w_*.mat.json')):
    d=json.load(open(f))
    for k,v in d.items():
        if v.get('clearGlass'):d[k]={'cockpitDonor':'US_AH-1W_Glass','fallback':{'metallic':0.0,'smoothness':0.95,'alpha':'BLEND','cutoff':0.5,'emissive':[0,0,0],'unlit':False,'clearGlass':True,'opacity':0.1}}
    json.dump(d,open(f,'w'),indent=1)
P
cd $R/tools; GLASS_K=0.38 GLASS_U0=0.0,-0.86 $PY glass_planar_uv.py ah1w | tail -4
cd $R/icons; python3 roc_icons.py ah1w | tail -1
echo AH1WDONE
