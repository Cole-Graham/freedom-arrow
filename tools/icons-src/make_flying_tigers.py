"""Flying Tigers card icon FA_PLA_INF_FLYING_TIGERS (+ _OUTLINE) (Osama 26 Nov 2026 03:2x PST, thread 1567745029781454889: "I also attached their
icon, please generate the icon for them", with the Hong Kong Special Duties Unit 飛虎 patch, 496x226). Same style as the other China SF card icons
(FA_PLA_INF_FALCON etc.): white figure on transparent 256x160, the _OUTLINE file identical. The patch's black ink becomes the white figure; the gold and
white fills stay transparent. The ribbon with 'HONG KONG SPECIAL DUTIES UNIT' is left out (unreadable at card size); tiger head and wings stay.
usage: python make_flying_tigers.py PATCH.png OUTDIR"""
import sys
import numpy as np
from PIL import Image

src = np.asarray(Image.open(sys.argv[1]).convert('RGBA')).astype(float)
lum = src[..., :3] @ [0.299, 0.587, 0.114]
m = np.clip((150 - lum) / 90, 0, 1) * src[..., 3] / 255
yy, xx = np.mgrid[:m.shape[0], :m.shape[1]]
m[(yy > 150) & ((xx < 205) | (xx > 292))] = 0          # ribbon ends
m[yy > 192] = 0                                         # ribbon middle below the chin
im = Image.fromarray((m * 255).astype(np.uint8))
im = im.crop(im.getbbox())
s = min(236 / im.width, 140 / im.height)
im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
alpha = Image.new('L', (256, 160), 0); alpha.paste(im, ((256 - im.width) // 2, (160 - im.height) // 2))
out = Image.new('RGBA', (256, 160), (255, 255, 255, 0)); out.putalpha(alpha)
for n in ('FA_PLA_INF_FLYING_TIGERS.png', 'FA_PLA_INF_FLYING_TIGERS_OUTLINE.png'):
    out.save(f'{sys.argv[2]}/{n}')
print('icon', out.size, alpha.getbbox())
