#!/usr/bin/env bash
# 26 Nov: Shawn's F-16A + Mirage 2000 -> raw GLB (fbx2glb_roc) -> plane_prep (drop stores, nose +X, up +Z) -> preview. One Blender at a time.
cd "$(dirname "$0")/../veh"; BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; R=$(cd ..; pwd); F2G=$R/tools/fbx2glb_roc.py
run(){ s=$1; drop=$2; td=${3:-x/$s/tex}; echo "== $s $(date +%T)"
  timeout 1200 nice -n 19 $BL -b -P $F2G -- x/$s/fbx.FBX x/$s/${s}_raw.glb $td "" > x/$s/fbx2glb.log 2>&1; grep -E "^MAT|NO TEX" x/$s/fbx2glb.log | cut -c1-160
  timeout 1200 nice -n 19 $BL -b -P $R/tools/plane_prep.py -- x/$s/${s}_raw.glb x/$s/$s.glb - "$drop" > x/$s/prep.log 2>&1; grep -E "DROPPED|ORIENT|Error" x/$s/prep.log
  timeout 600 nice -n 19 $BL -b -P $R/tools/view34.py -- $PWD/x/$s/$s.glb $PWD/$s.png > /dev/null 2>&1; ls -l $s.png | awk '{print $5,$9}'; }
run mirage '^(MICA|Fuelbox|mirage_missilerack)'
run f16a '^(L_Missile|R_Missile)'
echo ALLDONE
