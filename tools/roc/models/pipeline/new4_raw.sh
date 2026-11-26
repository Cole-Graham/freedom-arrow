#!/usr/bin/env bash
# 26 Nov: Shawn's 4 new models -> raw GLB (fbx2glb) -> plane_prep (drop stores/gear, nose +X, up +Z) -> preview. One Blender at a time.
cd "$(dirname "$0")/../veh"; W=/home/sam/tars/work/ba-dev/replicas/codex/work; BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender
F2G=$W/pla-0.8/purchased-20261113/fbx2glb.py; R=$(cd ..; pwd)
run(){ s=$1; drop=$2; echo "== $s $(date +%T)"
  timeout 900 nice -n 10 $BL -b -P $F2G -- x/$s/fbx.FBX x/$s/${s}_raw.glb x/$s "" > x/$s/fbx2glb.log 2>&1; grep -E "^MAT|NO TEX" x/$s/fbx2glb.log | cut -c1-160
  timeout 900 nice -n 10 $BL -b -P $R/tools/plane_prep.py -- x/$s/${s}_raw.glb x/$s/$s.glb - "$drop" > x/$s/prep.log 2>&1; grep -E "DROPPED|ORIENT|Error" x/$s/prep.log
  timeout 300 nice -n 10 $BL -b -P $R/tools/view34.py -- $PWD/x/$s/$s.glb $PWD/$s.png > /dev/null 2>&1; ls -l $s.png | awk '{print $5,$9}'; }
run ah64e '^(AGM114|M261|M299|M300|M301)'
run fck1 '^(TC-|US_150Gal|IDF_LandGear|IDF_Wheel|Box003$|Box01[012]$)'
run c130 '^$'
run chx2 '^$'
echo ALLDONE
