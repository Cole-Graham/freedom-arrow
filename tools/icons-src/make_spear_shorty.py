"""Sig Spear Shorty HUD icon (Osama 26 Nov 2026 01:5x, thread "China cosmetic work": "This is the new Sig Spear Shorty, add a suppressor to it
in front, it's a Sig Spear stat clone"; photo src.png 1171x551, muzzle left). The outline is segmented from the photo (gun = saturated tan or
dark pixels; the checkered background is light and grey), holes (stock skeleton, trigger guard) kept. A suppressor (photo x -95..116, 44 px
tall, rounded ends) replaces the flash hider. Detail lines = the photo's strongest inner edges. Style as the approved icons (FA_US_WP_MTL30):
fill #65706b @0.9, white 6.81 edge, #cdd8d0 @0.7 detail lines, 1160 px wide, muzzle LEFT in the file (the game mirrors it)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src = Image.open('src.png').convert('RGB'); a = np.asarray(src).astype(float) / 255
mx, mn = a.max(2), a.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
gun = ((sat > 0.13) | (mx < 0.62))
m = Image.fromarray((gun * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
# keep the largest connected part (the gun), drop stray checker specks
import scipy.ndimage as nd
lab, n = nd.label(np.asarray(m) > 127); sizes = nd.sum(np.ones_like(lab), lab, range(1, n + 1)); big = lab == (1 + int(np.argmax(sizes)))
# remove the flash hider (photo x < 116 around the bore) and add the suppressor
PAD = 110; H, W = big.shape
canvas = np.zeros((H, W + PAD), bool); canvas[:, PAD:] = big
canvas[:, :PAD + 116] = False
sup = Image.new('L', (W + PAD, H), 0); d = ImageDraw.Draw(sup)
y0, y1 = 232, 276; xa, xb = PAD - 95, PAD + 122
d.rounded_rectangle((xa, y0, xb, y1), radius=9, fill=255)
mask = canvas | (np.asarray(sup) > 127)
# fill small pin-holes but keep the big openings (stock skeleton, trigger guard)
holes = nd.binary_fill_holes(mask) & ~mask; hl, hn = nd.label(holes); hs = nd.sum(np.ones_like(hl), hl, range(1, hn + 1))
for i, s in enumerate(hs, 1):
    if s < 1800: mask[hl == i] = True
# detail lines: strong luminance edges inside the gun, away from the outline
lum = np.asarray(Image.open('src.png').convert('L')).astype(float)
L = np.zeros((H, W + PAD)); L[:, PAD:] = lum
gx = nd.sobel(L, 1); gy = nd.sobel(L, 0); g = np.hypot(gx, gy)
inner = nd.binary_erosion(mask, iterations=7)
edge = (g > 330) & inner; edge[:, :PAD + 120] = False
el, en = nd.label(edge, structure=np.ones((3, 3))); keep = np.zeros_like(edge)
for i, sl in enumerate(nd.find_objects(el), 1):   # long structural edges only: engraved text and screw heads are short blobs
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if max(h, w) >= 34 and (el[sl] == i).sum() >= 60: keep[sl] |= el[sl] == i
# suppressor details: two rings + a centre line
det = Image.new('L', mask.shape[::-1], 0); dd = ImageDraw.Draw(det)
for x in (xa + 26, xb - 30): dd.line((x, y0 + 7, x, y1 - 7), fill=255, width=3)
dd.line((xa + 40, (y0 + y1) // 2, xb - 44, (y0 + y1) // 2), fill=255, width=2)
detail = keep | (np.asarray(det) > 127)
# compose at 4x, crop to content, fit 1160 px wide
ys, xs = np.where(mask); bx0, bx1, by0, by1 = xs.min() - 12, xs.max() + 12, ys.min() - 12, ys.max() + 12
S = 1160 / (bx1 - bx0); OW, OH = 1160, int(round((by1 - by0) * S))
def fit(arr): return Image.fromarray((arr[by0:by1, bx0:bx1] * 255).astype(np.uint8)).resize((OW, OH), Image.LANCZOS)
mk = fit(mask); dt = fit(detail)
edge_w = 6.81; ring = mk.filter(ImageFilter.MaxFilter(2 * int(edge_w) + 1))
out = Image.new('RGBA', (OW, OH), (0, 0, 0, 0))
white = Image.new('RGBA', (OW, OH), (255, 255, 255, 255)); out = Image.composite(white, out, ring.point(lambda v: 255 if v > 127 else 0))
fillc = Image.new('RGBA', (OW, OH), (0x65, 0x70, 0x6b, 230)); out = Image.composite(fillc, out, mk.point(lambda v: 255 if v > 127 else 0))
linec = Image.new('RGBA', (OW, OH), (0xcd, 0xd8, 0xd0, 255)); lm = dt.point(lambda v: int(178 * min(1, v / 110)))
lm = Image.composite(lm, Image.new('L', (OW, OH), 0), mk.point(lambda v: 255 if v > 127 else 0)); out.alpha_composite(Image.composite(linec, Image.new('RGBA', (OW, OH), (0, 0, 0, 0)), lm))
out.save('FA_US_WP_SPEAR_SHORTY.png'); out.save('FA_US_WP_SPEAR_SHORTY_OUTLINE.png')
bg = Image.new('RGBA', (OW, OH), (40, 44, 52, 255)); bg.alpha_composite(out); bg.transpose(Image.FLIP_LEFT_RIGHT).convert('RGB').save('preview_muzzle_right.png')
print('icon', OW, OH)
