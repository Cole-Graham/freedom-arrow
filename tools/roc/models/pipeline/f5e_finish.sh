#!/usr/bin/env bash
# F-5E (Shawn 27 Nov 19:4x) as the ROC F-5F card's model (slug f5f): Arsenal from the gear-down GLB, battle + LODs from the gear-up GLB.
# Old F-5F files: veh/x/f5f/pre-f5e/. usage: f5e_finish.sh
R=/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125; cd $R/veh; W=/home/sam/tars/work/ba-dev/replicas/codex/work
BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; PY=$W/pla-division/.venv/bin/python; FC=$W/pla-division/famconv.py
LOD=$W/pla-hotfix39-worktree/tools/pla-specs/battle-lod/lod2.py; s=f5f; L=14.45
tris(){ $PY -c "
import sys;sys.path.insert(0,'$R/tools');from famread import read_fam
print(sum(len(x['idx'])//3 for b,ss in read_fam('$1') for x in ss))"; }
for t in "m_roc_${s}_static 2048 90000 x/f5e/f5e_gear.glb" "m_roc_${s}_lo_static 1024 40000 x/f5e/f5e_nogear.glb"; do set -- $t
  timeout 900 nice $PY $FC $4 models $1 --tex-max $2 --length $L > x/f5e/$1.json 2>&1; timeout 900 nice $PY $FC $4 models $1 --tex-max $2 --length $L --maps-only >/dev/null 2>&1
  n=$(tris models/$1.fam); if [ $n -gt $3 ]; then mv models/$1.fam x/f5e/$1.full.fam; CULL=0.004 KEEP=12 timeout 1200 nice $BL -b -P $LOD -- x/f5e/$1.full.fam models/$1.fam $3 > x/f5e/cut_$1.log 2>&1; fi
  echo "$1 $n -> $(tris models/$1.fam)"; done
$PY $R/tools/glass.py $s
n=$(tris models/m_roc_${s}_lo_static.fam)
for lv in "l1 60" "l2 30"; do set -- $lv
  CULL=0.004 KEEP=12 timeout 900 nice $BL -b -P $LOD -- models/m_roc_${s}_lo_static.fam models/m_roc_${s}_lo_static_$1.fam $((n*$2/100)) > x/f5e/lod_$1.log 2>&1; echo "$1 $(tris models/m_roc_${s}_lo_static_$1.fam)"; done
echo ALLDONE
