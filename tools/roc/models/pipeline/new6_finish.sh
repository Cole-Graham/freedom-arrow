#!/usr/bin/env bash
# 26 Nov: Mirage re-prep upside up (UPSIGN=1), then finish both (armory 2048 / battle 1024, LODs, glass, .fat). One Blender at a time.
cd "$(dirname "$0")/../veh"; BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; R=$(cd ..; pwd)
UPSIGN=1 timeout 1200 nice -n 19 $BL -b -P $R/tools/plane_prep.py -- x/mirage/mirage_raw.glb x/mirage/mirage.glb - '^(MICA|Fuelbox|mirage_missilerack)' > x/mirage/prep.log 2>&1; grep -E "DROPPED|ORIENT" x/mirage/prep.log
timeout 600 nice -n 19 $BL -b -P $R/tools/view34.py -- $PWD/x/mirage/mirage.glb $PWD/mirage.png > /dev/null 2>&1
timeout 600 nice -n 19 $BL -b -P $R/tools/viewbelow.py -- $PWD/x/mirage/mirage.glb $PWD/mirage_below.png > /dev/null 2>&1
for a in "mirage 14.36 120000 55000" "f16a 15.06 120000 55000"; do set -- $a; echo "== $1 $(date +%T)"; nice -n 19 $R/tools/finish_one.sh $1 $2 $3 $4 2>&1 | tail -8; done
for f in models/m_roc_{mirage,f16a}_lo_static_l[12].fam; do cp ${f%_l?.fam}.mat.json ${f%.fam}.mat.json; done; ls models/m_roc_{mirage,f16a}_*.mat.json | wc -l
echo ALLFIN
