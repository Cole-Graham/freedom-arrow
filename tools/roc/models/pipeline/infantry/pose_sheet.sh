#!/usr/bin/env bash
# pose_sheet.sh KEY RIGSDIR -> pose_KEY.png (rest + two posed views)
K=$1;RG=$2;B=/nix/store/faknn1kn5qdqdya32qz0llxpqv6732aa-blender-5.2.3/bin/blender
cd /home/sam/tars/work/ba-dev/replicas/codex/work/roc-20261125/inf
timeout 600 $B -b $RG/$K/rig.blend -P tools/posetest.py -- /tmp/troc-pose_$K.png 2>&1 | grep -E "POSED|Error"
python3 -c "
from PIL import Image
ims=[Image.open(p).convert('RGB') for p in ['$RG/$K/rest0.png','/tmp/troc-pose_${K}_0.png','/tmp/troc-pose_${K}_1.png']]
h=600;ims=[i.resize((int(i.width*h/i.height),h)) for i in ims];c=Image.new('RGB',(sum(i.width for i in ims),h),'white');x=0
for i in ims:c.paste(i,(x,0));x+=i.width
c.save('pose_$K.png')"
