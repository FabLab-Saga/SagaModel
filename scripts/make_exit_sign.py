"""Exit pictogram for the SSW escape doors: my own drawing (Talos, 2026-11-25), generated here, no third-party
artwork. Running figure entering a door, white on safety green, 2:1. Output: assets/signs/exit_pictogram.png.
Run with system python3 (PIL)."""
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "signs", "exit_pictogram.png")
W, H, SS = 1000, 500, 4                     # supersampled, then downscaled for clean edges
GREEN, WHITE = (0, 132, 61), (255, 255, 255)


def main():
    im = Image.new("RGB", (W * SS, H * SS), GREEN)
    d = ImageDraw.Draw(im)
    s = lambda *v: [c * SS for c in v]

    def limb(pts, w):
        pts = [(x * SS, y * SS) for x, y in pts]
        d.line(pts, fill=WHITE, width=int(w * SS), joint="curve")
        for x, y in pts:
            r = w * SS / 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)

    m = 40                                                       # white border inset
    d.rectangle(s(m, m, W - m, H - m), outline=WHITE, width=10 * SS)
    # door on the right: white frame, green opening, figure steps into it
    d.rectangle(s(600, 95, 880, 420), fill=WHITE)
    d.rectangle(s(640, 130, 845, 420), fill=GREEN)
    # running figure (leaning forward, towards the door)
    hx, hy = 455, 130
    d.ellipse(s(hx - 34, hy - 34, hx + 34, hy + 34), fill=WHITE)            # head
    sh, hip = (430, 195), (380, 300)                                        # shoulder, hip
    limb([sh, hip], 58)                                                     # torso
    limb([sh, (480, 245), (545, 225)], 30)                                  # front arm
    limb([sh, (370, 225), (320, 270)], 30)                                  # back arm
    limb([hip, (455, 340), (430, 420), (475, 420)], 34)                     # front leg, foot
    limb([hip, (320, 360), (240, 350)], 34)                                 # back leg
    # arrow on the left, pointing to the door
    d.rectangle(s(95, 235, 200, 275), fill=WHITE)
    d.polygon(s(195, 205, 250, 255, 195, 305), fill=WHITE)
    im = im.resize((W, H), Image.LANCZOS)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT)
    print(OUT, im.size)


if __name__ == "__main__":
    main()
