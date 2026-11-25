#!/usr/bin/env bash
# ROC vehicles: battle LOD1 (60%) / LOD2 (35%) of the battle mesh (lod2.py, as run_lod3.sh), then .fat textures for every model. One Blender at a time.
R=/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125; cd $R/veh; W=/home/sam/tars/work/ba-dev/replicas/codex/work
BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; LOD=$W/pla-hotfix39-worktree/tools/pla-specs/battle-lod/lod2.py
for s in cm34 cm33 cm22 cm26 cm11 antelope m41d tb2000 kf6 tk3; do
  n=$($W/pla-division/.venv/bin/python -c "
import sys;sys.path.insert(0,'$W/pla-0.8/purchased-20261113');from famread import read_fam
print(sum(len(x['idx'])//3 for b,ss in read_fam('models/m_roc_${s}_lo_static.fam') for x in ss))")
  for lv in "l1 60" "l2 35"; do set -- $lv
    CULL=0.004 KEEP=12 timeout 900 nice $BL -b -P $LOD -- models/m_roc_${s}_lo_static.fam models/m_roc_${s}_lo_static_$1.fam $((n*$2/100)) > x/$s/lod_$1.log 2>&1
    echo "$s battle $n -> $1 $(grep -o 'done.*' x/$s/lod_$1.log | tail -1)"; done
done
mkdir -p fat; (cd models && ls m_roc_*_tex*.png) > fat/list.txt
$W/pla-0.9/armory-opt/.venv/bin/python -I $W/pla-0.9/fat-all/conv.py fat/list.txt $PWD/models $PWD/fat 0 1 > fat/conv.log 2>&1
echo "fat $(ls fat/*.fat | wc -l) of $(wc -l < fat/list.txt)"; echo ALLDONE
