#!/usr/bin/env bash
# SF Section shoulders (Shawn 28 Nov 03:3x: "Add just the shoulder of this infantry model to a bit higher and more nature"): the 27 Nov flap
# fix pressed everything above the shoulder line to 8 % (k 0.08) and dropped it 1.2 cm; redo it at k 0.30, no drop, then re-rig and rebuild.
set -e
R=/home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125; W=/home/sam/tars/work/ba-dev/replicas/codex/work; cd $R/inf
BL=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender; PY=$W/pla-0.9/armory-opt/.venv/bin/python
S="$R/x/sf2/ROC SF2"; [ -f "$S/ROC SF 2 shoulders.blend.pre-1128" ] || cp "$S/ROC SF 2 shoulders.blend" "$S/ROC SF 2 shoulders.blend.pre-1128"
nice -n 10 $BL -b "$S/ROC SF 2.blend" -P tools/shoulder_flaps.py -- JGSF_soldier_01 "$S/ROC SF 2 shoulders.blend" k=0.30 drop=0 2>&1 | grep -E -i "moved|press|K=|error" | head -5
[ -d rigs_sf2.pre-1128 ] || cp -r rigs_sf2 rigs_sf2.pre-1128
NORENDER=1 nice -n 10 $BL -b -P tools/rig_roc.py -- sf2 roc_bodies.json $W/rigging-prep/out/BA_US_Ranger_Rifle1.glb $PWD/rigs_sf2 > rig_sf2_1128.log 2>&1; tail -2 rig_sf2_1128.log
for i in 0 1 2; do $PY -I tools/fas_armweights.py rigs_sf2/sf2/lod$i.fas /tmp/l9/sf2_aw$i.fas | tail -1; cp /tmp/l9/sf2_aw$i.fas rigs_sf2/sf2/lod$i.fas; done
bash tools/pipe_body_pbr.sh sf2 rigs_sf2 2>&1 | tail -4
echo SF2DONE
