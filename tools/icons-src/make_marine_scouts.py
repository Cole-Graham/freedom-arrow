"""Marine Scouts card icon FA_PLA_INF_LINE_MARINE_SCOUT (+ _OUTLINE) (Osama 26 Nov 2026 03:3x PST, thread 1567745029781454889: "their icon is a target
crosshair instead of the binos in front of the marine icon"). The Marine icon (FA_PLA_INF_LINE_MARINE) with a white crosshair where the Marine Recon
icon has its binoculars (lower right, over the ring), cut out of the ring with the same clear gap. 256x160 RGBA, _OUTLINE identical, as the others.
usage: python make_marine_scouts.py ICONDIR"""
import sys
from PIL import Image, ImageDraw

D = sys.argv[1]
base = Image.open(f'{D}/FA_PLA_INF_LINE_MARINE.png').convert('RGBA')
S = 4                                                     # draw at 4x, then downscale for smooth edges
cx, cy, r, w = 192 * S, 120 * S, 30 * S, 6 * S
gap = Image.new('L', (256 * S, 160 * S), 0); ImageDraw.Draw(gap).ellipse((cx - r - 4 * S, cy - r - 4 * S, cx + r + 4 * S, cy + r + 4 * S), fill=255)
fig = Image.new('L', (256 * S, 160 * S), 0); d = ImageDraw.Draw(fig)
d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=255, width=w)
t, L = 3 * S, 15 * S                                      # ticks: half width, length (from outside the ring inwards)
for x0, y0, x1, y1 in ((cx - t, cy - r - 3 * S, cx + t, cy - r + L), (cx - t, cy + r - L, cx + t, cy + r + 3 * S),
                       (cx - r - 3 * S, cy - t, cx - r + L, cy + t), (cx + r - L, cy - t, cx + r + 3 * S, cy + t)):
    d.rectangle((x0, y0, x1, y1), fill=255)
d.ellipse((cx - 3 * S, cy - 3 * S, cx + 3 * S, cy + 3 * S), fill=255)
gap, fig = gap.resize((256, 160), Image.LANCZOS), fig.resize((256, 160), Image.LANCZOS)
a = base.getchannel('A').point(lambda v: v)
a = Image.composite(Image.new('L', a.size, 0), a, gap)    # clear the ring behind the crosshair
a = Image.composite(fig, a, fig)
out = Image.new('RGBA', base.size, (255, 255, 255, 0)); out.putalpha(a)
rgb = Image.composite(Image.new('RGBA', base.size, (255, 255, 255, 255)), base, fig)
out = Image.merge('RGBA', (*rgb.split()[:3], a))
for n in ('FA_PLA_INF_LINE_MARINE_SCOUT.png', 'FA_PLA_INF_LINE_MARINE_SCOUT_OUTLINE.png'):
    out.save(f'{D}/{n}')
print('icon', out.size, a.getbbox())
