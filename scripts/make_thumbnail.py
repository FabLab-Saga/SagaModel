"""Video thumbnail (1920x1080 PNG): a frame of the final walkthrough with a dark gradient, the white FAB LAB SAGA
lockup and the tagline. Claude's design, for comparison with the title-card frame.
    /usr/bin/python3 scripts/make_thumbnail.py <frame_no> <out.png> [top|left]
"""
import os
import os as _os
SAGA_VIDEO = _os.environ.get("SAGA_VIDEO_DIR") or _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".local", "saga-video")   # agent-work media outside the repo; .local/ is gitignored (symlink it)
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FT = os.path.join(SAGA_VIDEO, "fframes-title/media")
W, H = 1920, 1080
fno, out = int(sys.argv[1]), sys.argv[2]
mode = sys.argv[3] if len(sys.argv) > 3 else "top"

bg = Image.open(os.path.join(ROOT, f"renders/walk/final/f{fno:05d}.png")).convert("RGBA")
grad = Image.new("L", (W, H), 0)
g = ImageDraw.Draw(grad)
for i in range(H if mode == "top" else W):
    if mode == "top":   # dark band across the top, fading out by 48 % of the height
        v = int(215 * max(0.0, 1 - i / (H * 0.48)) ** 1.6)
        g.line([(0, i), (W, i)], fill=v)
    else:               # dark band on the left, fading out by 58 % of the width
        v = int(225 * max(0.0, 1 - i / (W * 0.58)) ** 1.5)
        g.line([(i, 0), (i, H)], fill=v)
shade = Image.new("RGBA", (W, H), (0, 0, 0, 255))
shade.putalpha(grad)
im = Image.alpha_composite(bg, shade)

lk = Image.open(os.path.join(FT, "lockup_white.png")).convert("RGBA")
lw = 820 if mode == "top" else 760
lk = lk.resize((lw, round(lw * lk.height / lk.width)), Image.LANCZOS)
tag = "SKÖPUNAR- OG TÆKNISMIÐJA"
ft = ImageFont.truetype(os.path.join(FT, "RobotoCondensed-Regular.ttf"), 44)
d = ImageDraw.Draw(im)
if mode == "top":
    x, y = (W - lw) // 2, 70
    im.alpha_composite(lk, (x, y))
    d.text((W // 2, y + lk.height + 34), tag, font=ft, fill="white", anchor="mt", spacing=0)
else:
    x, y = 110, (H - lk.height) // 2 - 50
    im.alpha_composite(lk, (x, y))
    d.text((x + 14, y + lk.height + 40), tag, font=ft, fill="white", anchor="lt")
im.convert("RGB").save(out)
print(out)
