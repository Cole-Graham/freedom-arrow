"""QLZ-87 HUD icon (Osama 26 Nov 2026 02:2x, thread "China cosmetic work": "this is the new QLZ-87, it's a stat clone of the QLZ-04 ...", photo src.png
1132x728, muzzle right, gun tilted ~16.5 deg). Segmented from the photo (dark gun on white), bipod legs erased before levelling (as the QJY-88 and
QBZ-192 MLOK icons leave the bipod out), levelled, mirrored to muzzle LEFT (the game mirrors HUD icons). Detail lines = strong inner edges.
Style as the approved icons: fill #65706b @0.9, white 6.81 edge, #cdd8d0 @0.7 lines, 1160 px wide."""
import numpy as np, scipy.ndimage as nd
from PIL import Image, ImageDraw, ImageFilter
src = Image.open('src.png').convert('RGB'); lum0 = np.asarray(src.convert('L')).astype(float)
gun = lum0 < 205
er = Image.new('L', src.size, 0); d = ImageDraw.Draw(er)
d.polygon([(700, 330), (905, 330), (905, 650), (700, 650)], fill=255)          # bipod legs (below the barrel, right of the drum)
gun &= ~(np.asarray(er) > 0)
lab, n = nd.label(gun); sz = nd.sum(np.ones_like(lab), lab, range(1, n + 1)); gun = lab == 1 + int(np.argmax(sz))
gun = nd.binary_closing(gun, iterations=2)
ANG = -16.5
def rot(arr, fill=0, res=Image.NEAREST): return np.asarray(Image.fromarray(arr).rotate(ANG, res, expand=True, fillcolor=fill))
mask = rot((gun * 255).astype(np.uint8)) > 127
lum = rot(lum0.astype(np.uint8), 255, Image.BICUBIC).astype(float)
mask = mask[:, ::-1]; lum = lum[:, ::-1]                                          # muzzle left
holes = nd.binary_fill_holes(mask) & ~mask; hl, hn = nd.label(holes); hs = nd.sum(np.ones_like(hl), hl, range(1, hn + 1))
for i, s in enumerate(hs, 1):
    if s < 900: mask[hl == i] = True
g = np.hypot(nd.sobel(lum, 1), nd.sobel(lum, 0)); inner = nd.binary_erosion(mask, iterations=6)
edge = (g > 170) & inner; el, en = nd.label(edge, structure=np.ones((3, 3))); keep = np.zeros_like(edge)
for i, sl in enumerate(nd.find_objects(el), 1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if max(h, w) >= 26 and (el[sl] == i).sum() >= 45: keep[sl] |= el[sl] == i
ys, xs = np.where(mask); bx0, bx1, by0, by1 = xs.min() - 12, xs.max() + 12, ys.min() - 12, ys.max() + 12
S = 1160 / (bx1 - bx0); OW, OH = 1160, int(round((by1 - by0) * S))
def fit(arr): return Image.fromarray((arr[by0:by1, bx0:bx1] * 255).astype(np.uint8)).resize((OW, OH), Image.LANCZOS)
mk = fit(mask); dt = fit(keep); M = mk.point(lambda v: 255 if v > 127 else 0)
ring = mk.filter(ImageFilter.MaxFilter(15)).point(lambda v: 255 if v > 127 else 0)
out = Image.composite(Image.new('RGBA', (OW, OH), (255, 255, 255, 255)), Image.new('RGBA', (OW, OH), (0, 0, 0, 0)), ring)
out = Image.composite(Image.new('RGBA', (OW, OH), (0x65, 0x70, 0x6b, 230)), out, M)
lm = Image.composite(dt.point(lambda v: int(178 * min(1, v / 110))), Image.new('L', (OW, OH), 0), M)
out.alpha_composite(Image.composite(Image.new('RGBA', (OW, OH), (0xcd, 0xd8, 0xd0, 255)), Image.new('RGBA', (OW, OH), (0, 0, 0, 0)), lm))
out.save('FA_PLA_WP_QLZ87.png'); out.save('FA_PLA_WP_QLZ87_OUTLINE.png')
bg = Image.new('RGBA', (OW, OH), (40, 44, 52, 255)); bg.alpha_composite(out); bg.transpose(Image.FLIP_LEFT_RIGHT).convert('RGB').save('preview_muzzle_right.png')
print('icon', OW, OH)
