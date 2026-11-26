"""MTL-30 HUD icon (Osama 25 Nov 2026 19:4x, bugs thread 1573561286803980289: "Create this as the MTL-30 and it replaces the XM-25 punisher
cosmetically", photo ref/mtl30.png 1353x561, Barrett squad support rifle on a show stand, muzzle right). The photo has a busy background, so the
silhouette is traced by hand in photo coordinates (stock with its skeleton window, receiver, rail, optic, grip, trigger guard, magazine);
detail lines are placed by hand. Mirrored at the end: our files are muzzle LEFT (the game mirrors them). Style = the approved icons:
fill #65706b @0.9, white 6.81 edge, #cdd8d0 @0.7 detail lines, 1160 px wide."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
K = 4
X0, Y0, X1, Y1 = 30, 10, 1325, 560
W, H = (X1 - X0) * K, (Y1 - Y0) * K
P = lambda pts: [((x - X0) * K, (y - Y0) * K) for x, y in pts]
sil = Image.new('L', (W, H), 0); sd = ImageDraw.Draw(sil)
def poly(pts, v=255): sd.polygon(P(pts), fill=v)
def thick(pts, w):
    sd.line(P(pts), fill=255, width=int(w * K), joint='curve')
    for q in P([pts[0], pts[-1]]): r = w * K / 2; sd.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)
# stock: outer shape, then the skeleton window
poly([(45, 252), (90, 247), (425, 243), (428, 302), (332, 302), (268, 396), (272, 413), (78, 413), (46, 406)])
poly([(104, 310), (296, 310), (238, 386), (104, 386)], 0)
# receiver: rail, upper body, lower receiver
poly([(430, 184), (1290, 184), (1292, 200), (430, 202)])                                        # rail
poly([(436, 200), (1296, 200), (1300, 218), (1300, 296), (1288, 307), (978, 309), (976, 332), (452, 334), (436, 318), (424, 268), (428, 218)])
poly([(1298, 226), (1312, 226), (1312, 244), (1298, 244)])                                      # muzzle stub
# optic + mount
poly([(486, 88), (612, 93), (626, 42), (700, 24), (742, 38), (746, 94), (878, 91), (892, 100), (892, 160), (772, 170), (774, 196),
      (588, 196), (600, 170), (486, 163)])
# grip, trigger guard, magazine
poly([(472, 330), (545, 330), (554, 378), (530, 432), (506, 480), (458, 480), (446, 462), (468, 398)])
thick([(548, 336), (560, 380), (590, 393), (620, 385), (632, 334)], 9)
poly([(630, 330), (746, 330), (778, 538), (770, 544), (646, 544), (638, 538)])
sil = sil.filter(ImageFilter.GaussianBlur(1.2 * K / 2))
m = np.asarray(sil) > 127
def mf(mask, size, op):
    img = Image.fromarray((mask * 255).astype(np.uint8)); f = ImageFilter.MinFilter(size) if op == 'min' else ImageFilter.MaxFilter(size)
    return np.asarray(img.filter(f)) > 127
EW = int(round(6.81 / 2 / 1160 * W)) | 1
outer = mf(m, 2 * EW + 1, 'max'); inner = mf(m, 2 * EW + 1, 'min')
lines = Image.new('L', (W, H), 0); ld = ImageDraw.Draw(lines); LW = max(2, int(round(3.0 / 1160 * W)))
def L(*p):
    pts = P(p); ld.line(pts, fill=255, width=LW)
    for q in (pts[0], pts[-1]): r = LW / 2; ld.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)
def R(x0, y0, x1, y1): L((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))
def C(cx, cy, r, n=14): L(*[(cx + r * math.cos(k / n * 2 * math.pi), cy + r * math.sin(k / n * 2 * math.pi)) for k in range(n + 1)])
for x in range(446, 1282, 16): L((x, 187), (x, 197))                                            # rail teeth
L((436, 203), (1296, 203))                                                                     # rail base
R(645, 250, 806, 296)                                                                          # ejection port
for x in range(990, 1275, 24): R(x, 226, x + 12, 236); R(x, 258, x + 12, 268)                   # vent slots, two rows
L((976, 205), (976, 306))                                                                       # handguard / receiver seam
L((452, 312), (974, 312))                                                                       # lower receiver edge
C(546, 337, 3)                                                                                  # selector pin
for x in (174, 182, 190): L((x, 262), (x, 280))                                                 # stock grip marks
L((62, 254), (62, 406))                                                                         # butt pad
L((612, 98), (612, 158)); L((744, 98), (744, 160)); L((520, 100), (520, 156))                   # optic sections
C(760, 128, 14); L((640, 50), (725, 50)); L((650, 60), (650, 90))                              # turret dial, top housing
L((600, 182), (770, 182))                                                                       # optic mount
L((642, 360), (768, 360)); L((646, 520), (774, 520))                                            # magazine ribs
for k in range(4): L((478 + 4 * k, 400 + 16 * k), (512 + 4 * k, 404 + 16 * k))                  # grip texture
det = (np.asarray(lines) > 127) & mf(m, 3, 'min')
rgba = np.zeros(m.shape + (4,), np.float32); rgba[m] = (101, 112, 106, 230); rgba[outer & ~inner] = (255, 255, 255, 255)
al = 0.7; ba = rgba[det, 3:4] / 255
rgba[det, :3] = (np.array((205, 216, 208)) * al + rgba[det, :3] * ba * (1 - al)) / (al + ba * (1 - al)); rgba[det, 3] = (al + ba[:, 0] * (1 - al)) * 255
img = Image.fromarray(rgba.astype(np.uint8), 'RGBA'); img = img.crop(img.getbbox())
img = img.transpose(Image.FLIP_LEFT_RIGHT)                                                      # muzzle left = our file orientation
img = img.resize((1160, round(img.height * 1160 / img.width)), Image.LANCZOS)
img.save('FA_US_WP_MTL30.png'); img.save('FA_US_WP_MTL30_OUTLINE.png')
prev = Image.new('RGBA', (img.width + 80, img.height + 80), (40, 44, 48, 255)); prev.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT), (40, 40))
prev.save('preview_muzzle_right.png'); print(img.size)
