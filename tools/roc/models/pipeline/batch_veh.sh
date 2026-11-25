#!/usr/bin/env bash
# ROC ground vehicles: FBX -> GLB (fbx2glb) -> armory 2048 / battle 1024 .fam (famconv) -> preview. One Blender at a time.
cd "$(dirname "$0")/../veh"
W=/home/sam/tars/work/ba-dev/replicas/codex/work; BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender
F2G=$W/pla-0.8/purchased-20261113/fbx2glb.py; PY=$W/pla-division/.venv/bin/python; FC=$W/pla-division/famconv.py
for spec in "$@"; do s=${spec%%:*}; L=${spec#*:}
  echo "== $s $(date +%T)"
  timeout 900 nice $BL -b -P $F2G -- x/$s/fbx.FBX x/$s/$s.glb x/$s "" > x/$s/fbx2glb.log 2>&1; grep -E "^MAT|NO TEX" x/$s/fbx2glb.log | cut -c1-160
  for t in "m_roc_${s}_static 2048" "m_roc_${s}_lo_static 1024"; do set -- $t
    timeout 900 nice $PY $FC x/$s/$s.glb models $1 --tex-max $2 --length $L > x/$s/$1.json 2>&1; tail -1 x/$s/$1.json | cut -c1-220
    timeout 900 nice $PY $FC x/$s/$s.glb models $1 --tex-max $2 --length $L --maps-only > /dev/null 2>&1; done
  timeout 300 nice $BL -b -P ../tools/view34.py -- $PWD/x/$s/$s.glb $PWD/$s.png > /dev/null 2>&1; ls -l $s.png | awk '{print $5,$9}'
done; echo ALLDONE
