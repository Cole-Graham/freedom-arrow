"""MTL-30 HUD icon v3 (25 Nov 20:3x Osama "change the magazine and grip": grip + trigger guard and magazine re-measured from the photo). v2, higher-fidelity pass (Osama 25 Nov 2026 20:1x, bugs thread 1573561286803980289: "can you to a higher fidelity pass on
this icon"). Re-traced from 2x zoomed crops of ref/mtl30.png (photo coordinates, muzzle right): skeleton stock (butt pad, rear upright, bottom
bar with lightening holes, diagonal strut, arched web to the receiver), receiver with rounded nose, top rail, handguard with two vent rows and the
raised upper panel, muzzle stub, angled pistol grip with finger grooves, trigger guard, slanted magazine, and the optic: two bells, focus ring,
body, side turret, red-dot box with its handle, mount. Mirrored at the end (our files are muzzle left). Style = the approved icons:
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
def thick(pts, w, v=255):
    sd.line(P(pts), fill=v, width=int(w * K), joint='curve')
    for q in P([pts[0], pts[-1]]): r = w * K / 2; sd.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=v)
def ell(cx, cy, rx, ry, v=255): q = P([(cx - rx, cy - ry), (cx + rx, cy + ry)]); sd.ellipse([q[0], q[1]], fill=v)
# --- stock
poly([(46, 254), (52, 250), (78, 249), (78, 406), (52, 404), (47, 398)])                     # butt pad
poly([(78, 249), (300, 247), (426, 246), (428, 300), (78, 302)])                             # top tube
poly([(78, 300), (101, 300), (101, 411), (78, 411)])                                         # rear upright
poly([(78, 387), (262, 387), (270, 398), (264, 411), (78, 411)])                             # bottom bar
poly([(236, 392), (258, 411), (306, 300), (284, 300)])                                       # diagonal strut
poly([(284, 300), (428, 300), (430, 330), (392, 320), (340, 316), (306, 326), (284, 356), (268, 404), (252, 404)])  # strut + arched web to the receiver, filled
# --- receiver, rail, handguard, muzzle
poly([(430, 184), (1290, 184), (1292, 201), (430, 202)])                                     # rail
poly([(440, 200), (1295, 201), (1300, 212), (1297, 298), (1288, 306), (980, 307), (978, 331), (455, 334), (442, 324),
      (428, 290), (425, 250), (430, 214)])
poly([(1298, 228), (1312, 228), (1312, 244), (1298, 244)])                                    # muzzle stub
# --- grip + trigger guard, magazine: v3 outlines measured from the photo (dark grip and tan magazine against the white display)
poly([(446, 333), (515, 333), (512, 350), (522, 364), (556, 402), (549, 418), (546, 432), (534, 444), (531, 456), (520, 468),
      (512, 484), (496, 489), (462, 481), (449, 469), (452, 455), (470, 428), (486, 404), (470, 374), (447, 350)])
thick([(521, 336), (527, 378), (548, 390), (576, 388), (586, 336)], 6)                       # trigger guard
poly([(636, 331), (806, 331), (792, 352), (788, 372), (781, 400), (779, 535), (770, 546), (645, 546), (641, 538), (637, 400)])
# --- optic
poly([(484, 84), (500, 81), (500, 171), (484, 168)])                                        # rear bell
poly([(500, 92), (576, 91), (576, 158), (500, 156)])                                        # rear tube
poly([(576, 85), (612, 86), (612, 163), (576, 164)])                                        # focus ring
poly([(610, 95), (880, 96), (880, 164), (610, 164)])                                        # body
poly([(878, 86), (893, 89), (893, 170), (878, 172)])                                        # front bell
poly([(619, 32), (640, 26), (738, 26), (744, 34), (744, 100), (619, 100)])                  # red-dot box
poly([(648, 18), (700, 17), (704, 28), (644, 29)])                                          # box handle
poly([(588, 164), (774, 164), (772, 196), (592, 196), (584, 180)])                          # mount
sil = sil.filter(ImageFilter.GaussianBlur(1.0 * K / 2))
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
def R(x0, y0, x1, y1, rr=2):
    L((x0 + rr, y0), (x1 - rr, y0), (x1, y0 + rr), (x1, y1 - rr), (x1 - rr, y1), (x0 + rr, y1), (x0, y1 - rr), (x0, y0 + rr), (x0 + rr, y0))
def C(cx, cy, r, n=16): L(*[(cx + r * math.cos(k / n * 2 * math.pi), cy + r * math.sin(k / n * 2 * math.pi)) for k in range(n + 1)])
# stock details
for x in (172, 181, 190): L((x, 262), (x, 282))                                              # grip marks
L((90, 262), (410, 260))                                                                     # tube top bevel
for x in range(116, 258, 10): C(x, 398, 2.2, 10)                                             # lightening holes in the bottom bar
L((300, 286), (424, 284)); L((306, 316), (342, 308), (392, 311), (428, 318))                # buffer tube line, web edge
# receiver / handguard
for x in range(442, 1284, 11): L((x, 186), (x, 198))                                         # rail slots
L((440, 203), (1294, 203))
R(645, 250, 806, 296, 3)                                                                     # ejection port
L((980, 243), (1296, 243)); L((980, 204), (980, 306))                                        # handguard upper panel + seam
for x in range(990, 1262, 30): R(x, 224, x + 18, 236); R(x, 260, x + 18, 271)              # vent slots
L((456, 314), (976, 314))                                                                    # lower receiver edge
ell(546, 338, 8, 4, 0) if False else None
C(546, 338, 4)                                                                               # selector
L((432, 228), (440, 220)); L((427, 290), (436, 300))                                         # nose bevel
# grip / magazine
L((534, 340), (540, 372))                                                                     # trigger
L((537, 436), (548, 430)); L((522, 460), (534, 452))                                          # finger grooves
L((637, 400), (781, 400)); L((642, 528), (779, 528))                                          # magwell seam + base plate
for y in range(420, 520, 20): L((660, y), (760, y))                                          # magazine ribs
# optic
for x in (488, 494): L((x, 90), (x, 162))                                                    # rear bell rings
for x in (584, 592, 600): L((x, 92), (x, 158))                                               # focus ring grip
L((612, 130), (742, 130)); C(760, 128, 15); C(760, 128, 6)                                   # body seam + side turret
L((780, 106), (872, 106)); L((780, 152), (872, 152))                                         # body front panel
for x in (882, 888): L((x, 98), (x, 162))                                                    # front bell rings
R(630, 44, 734, 70, 3); C(651, 86, 6)                                                        # red-dot window + brightness knob
L((598, 184), (764, 184)); C(608, 189, 3); C(722, 189, 3)                                    # mount arm + screws
det = (np.asarray(lines) > 127) & mf(m, 3, 'min')
rgba = np.zeros(m.shape + (4,), np.float32); rgba[m] = (101, 112, 106, 230); rgba[outer & ~inner] = (255, 255, 255, 255)
al = 0.7; ba = rgba[det, 3:4] / 255
rgba[det, :3] = (np.array((205, 216, 208)) * al + rgba[det, :3] * ba * (1 - al)) / (al + ba * (1 - al)); rgba[det, 3] = (al + ba[:, 0] * (1 - al)) * 255
img = Image.fromarray(rgba.astype(np.uint8), 'RGBA'); img = img.crop(img.getbbox())
img = img.transpose(Image.FLIP_LEFT_RIGHT)
img = img.resize((1160, round(img.height * 1160 / img.width)), Image.LANCZOS)
img.save('FA_US_WP_MTL30.png')
prev = Image.new('RGBA', (img.width + 80, img.height + 80), (40, 44, 48, 255)); prev.alpha_composite(img.transpose(Image.FLIP_LEFT_RIGHT), (40, 40))
prev.save('preview_muzzle_right.png'); print(img.size)
