"""Marines PF-98 card icon FA_PLA_INF_LINE_MARINE_PF98 (+ _OUTLINE) (Osama 26 Nov 2026 13:0x PST, thread 1567745029781454889: "The new PF98 for
marines just call Marines PF-98. The icon is the Marine sign with the SMAW icon in the bottom right corner"). The Marine icon (FA_PLA_INF_LINE_MARINE)
with the vanilla SMAW team label silhouette (US_SMAW_TEAM-Label, unitlabels bundle) scaled into the lower right, over the ring, cut out of the ring
with a clear gap as the Marine Recon binoculars are. 256x160 RGBA, _OUTLINE identical, as the others.
usage: python make_marines_pf98.py ICONDIR SMAW_LABEL_PNG"""
import sys
from PIL import Image, ImageFilter

D, SMAW = sys.argv[1:3]
base = Image.open(f'{D}/FA_PLA_INF_LINE_MARINE.png').convert('RGBA')
sm = Image.open(SMAW).convert('RGBA'); sm = sm.crop(sm.getchannel('A').getbbox())
w = 112; sm = sm.resize((w, round(sm.height * w / sm.width)), Image.LANCZOS)
fig = Image.new('L', base.size, 0); x, y = 256 - w - 2, 160 - sm.height - 6
fig.paste(sm.getchannel('A'), (x, y))
gap = fig.filter(ImageFilter.MaxFilter(9))                  # about 4 px clear gap round the launcher
a = Image.composite(Image.new('L', base.size, 0), base.getchannel('A'), gap)
a = Image.composite(fig, a, fig)
out = Image.new('RGBA', base.size, (255, 255, 255, 0)); out.putalpha(a)
rgb = Image.composite(Image.new('RGBA', base.size, (255, 255, 255, 255)), base, fig)
out = Image.merge('RGBA', (*rgb.split()[:3], a))
for n in ('FA_PLA_INF_LINE_MARINE_PF98', 'FA_PLA_INF_LINE_MARINE_PF98_OUTLINE'): out.save(f'{D}/{n}.png')
print('saved', D)
