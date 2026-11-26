#!/usr/bin/env bash
# One ROC model from a finished GLB: armory 2048 / battle 1024 .fam, optional cuts, glass, LOD1/LOD2, .fat. usage: finish_one.sh SLUG LENGTH ARMORY_MAX BATTLE_MAX
# FCX: extra famconv arguments, e.g. FCX=--turn for aircraft wider than long (C-130, UAVs; 26 Nov)
R=/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125; cd $R/veh; W=/home/sam/tars/work/ba-dev/replicas/codex/work
BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; PY=$W/pla-division/.venv/bin/python; FC=$W/pla-division/famconv.py
LOD=$W/pla-hotfix39-worktree/tools/pla-specs/battle-lod/lod2.py; s=$1; L=$2; AMAX=$3; BMAX=$4
tris(){ $PY -c "
import sys;sys.path.insert(0,'$W/pla-0.8/purchased-20261113');from famread import read_fam
print(sum(len(x['idx'])//3 for b,ss in read_fam('$1') for x in ss))"; }
rm -f models/m_roc_${s}_*
for t in "m_roc_${s}_static 2048 $AMAX" "m_roc_${s}_lo_static 1024 $BMAX"; do set -- $t
  timeout 900 nice $PY $FC x/$s/$s.glb models $1 --tex-max $2 --length $L $FCX > /dev/null 2>&1; timeout 900 nice $PY $FC x/$s/$s.glb models $1 --tex-max $2 --length $L $FCX --maps-only >/dev/null 2>&1
  n=$(tris models/$1.fam); if [ $n -gt $3 ]; then mv models/$1.fam x/$s/$1.full.fam; CULL=0.004 KEEP=12 timeout 1200 nice $BL -b -P $LOD -- x/$s/$1.full.fam models/$1.fam $3 > x/$s/cut_$1.log 2>&1; fi
  echo "$1 $n -> $(tris models/$1.fam)"; done
$PY $R/tools/glass.py $s
n=$(tris models/m_roc_${s}_lo_static.fam)
for lv in "l1 60" "l2 35"; do set -- $lv
  CULL=0.004 KEEP=12 timeout 900 nice $BL -b -P $LOD -- models/m_roc_${s}_lo_static.fam models/m_roc_${s}_lo_static_$1.fam $((n*$2/100)) > x/$s/lod_$1.log 2>&1; echo "$1 $(tris models/m_roc_${s}_lo_static_$1.fam)"; done
(cd models && ls m_roc_${s}_*tex*.png) > fat/list_$s.txt
$W/pla-0.9/armory-opt/.venv/bin/python -I $W/pla-0.9/fat-all/conv.py fat/list_$s.txt $PWD/models $PWD/fat 0 1 > fat/conv_$s.log 2>&1; echo "fat $(ls fat/m_roc_${s}_* | wc -l)/$(wc -l < fat/list_$s.txt)"; echo ALLDONE $s
