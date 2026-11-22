# Wide launcher header (1180x280 design, drawn at 2x): menu art scaled to the header height, right-aligned,
# faded into the site's background on the left, with the approved title logo on the left.
from PIL import Image, ImageDraw
import sys
bg = Image.open(sys.argv[1]).convert('RGB')          # site/menu-bg.jpg 2560x1440
title = Image.open(sys.argv[2]).convert('RGBA')      # site/title.webp 501x560
out = sys.argv[3]
W, H = 2360, 560
BG = (0x0A, 0x0B, 0x0D)
y0, y1 = 270, 1170                                   # flag top .. soldiers' knees, like the old banner
crop = bg.crop((0, y0, 2560, y1))
s = H / crop.height
art = crop.resize((round(crop.width * s), H), Image.LANCZOS)
canvas = Image.new('RGB', (W, H), BG)
x = W - art.width
canvas.paste(art, (x, 0))
# fade the art's left edge into the background
fade = 300
mask = Image.new('L', (W, H), 0)
d = ImageDraw.Draw(mask)
for i in range(fade):
    d.line([(x + i, 0), (x + i, H)], fill=round(255 * (1 - i / fade) ** 1.6))
d.rectangle([0, 0, x, H], fill=255)
canvas = Image.composite(Image.new('RGB', (W, H), BG), canvas, mask)
# darken the bottom a little so the red line under the header reads, like the old banner
grad = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(grad)
for yy in range(H - 120, H):
    gd.line([(0, yy), (W, yy)], fill=round(150 * ((yy - (H - 120)) / 120) ** 1.5))
canvas = Image.composite(Image.new('RGB', (W, H), BG), canvas, grad)
th = 436
t = title.resize((round(title.width * th / title.height), th), Image.LANCZOS)
canvas.paste(t, (104, 32), t)
canvas.save(out, quality=90)
print(out, canvas.size, 'art x', x, 'title', t.size)
