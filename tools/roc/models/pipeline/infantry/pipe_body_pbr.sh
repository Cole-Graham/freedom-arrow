#!/usr/bin/env bash
# pipe_body_pbr.sh KEY RIGSDIR (27 Nov, PBR atlas: + _mask, area-weighted tiles): atlas -> 28k/7k/3k LODs -> _0_b battle copies -> .fat, into lod/ and fat/
set -e
K=$1; RG=$(realpath $2); W=/home/sam/tars/work/ba-dev/replicas/codex/work; R=$W/roc-20261125/inf
B=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; PY=$W/rigging-prep/.venv/bin/python
cd $R; A=$R/atlas_$K; rm -rf $A; $PY -I tools/atlas_pbr.py $RG $A 2>&1 | tail -1
mkdir -p lod fat/$K
for j in "0 28000" "1 7000" "2 3000"; do set -- $j; nice $B -b -P $W/pla-0.9/inf-lod/decimate_fas.py -- $A/roc_${K}_$1.fas $R/lod/roc_${K}_$1.fas $2 2>&1 | grep FASCUT; done
cp $A/roc_${K}_*.png lod/
$PY -I -c "
from PIL import Image
for s in ('','_n','_mask'):
    im=Image.open('lod/roc_${K}_0'+s+'.png');im.resize((im.width//2,im.height//2),Image.LANCZOS).save('lod/roc_${K}_0_b'+s+'.png')"
(cd lod && ls roc_${K}_*.png) > fat/$K/list.txt
$W/pla-0.9/armory-opt/.venv/bin/python -I $W/pla-0.9/fat-all/conv.py fat/$K/list.txt $R/lod $R/fat 0 1 > fat/$K/conv.log 2>&1
ls fat/roc_${K}_*.fat | wc -l
python3 -I -c "
import re
b=open('lod/roc_${K}_1.fas','rb').read();print(set(x.decode() for x in re.findall(rb'[a-z0-9_]{6,}\.png',b)))"
