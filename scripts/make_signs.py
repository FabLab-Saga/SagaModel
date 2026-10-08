"""Re-letter the brand-manual equipment signs (refs/branding/signage/*.pdf -> assets/signs/*.png).

The source PDFs have their header text outlined, with typos ("VERKÆRI", "ELECTRONCS"). This keeps
each PDF's illustration and background, paints over the header band, and sets new names in the
manual's sign typography: Icelandic in Roboto Condensed Regular (76 pt on the 25 cm sign), English
below at 53 pt, 70 % strength, both centred, sign-grey text (#E6E6E6).

Run with a Python that has Pillow (system python3), from the repo root:
    /usr/bin/python3 scripts/make_signs.py
Then re-run build_signs.py in Blender (the images are reloaded by file path).
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "refs/branding/signage/{}.pdf")
OUT = os.path.join(ROOT, "assets/signs/{}.png")
FONT = os.path.join(ROOT, "refs/branding/fonts/RobotoCondensed-Regular.ttf")
PX = 1024
PT = PX / 708.718                     # PDF page is 708.718 pt square
TEXT = (230, 230, 230)
MARGIN = 60                           # >= the manual's 1 cm on a 25 cm sign (41 px)
IS_BASE, EN_BASE = 119, 197           # baselines measured on the original signs
BAND = (20, 215)                      # rows holding the old header text

# file key -> (Icelandic, English). Names from Magnús 2026-10-08.
SIGNS = {
    "laser": ("GEISLASKERI", "LASER CUTTER"),
    "3d_prentari": ("ÞRÍVÍDDARPRENTARI", "3D PRINTER"),
    "fraesi_vel": ("FRÆSIVÉL", "MILLING MACHINE"),
    "rafeinda": ("RAFEINDAVERKSTÆÐI", "ELECTRONICS"),
    "saumavel": ("TEXTÍLSVÆÐI", "TEXTILES"),
    "verkfaeri": ("VERKFÆRI", "HAND TOOLS"),
    "vinylskeri": ("VÍNYLSKERI", "VINYL CUTTER"),
}


def fitted(text, size):
    """Font at `size` px, shrunk until the text fits between the margins."""
    while True:
        f = ImageFont.truetype(FONT, size)
        if f.getlength(text) <= PX - 2 * MARGIN or size < 20:
            return f
        size -= 2


def make(key, icelandic, english):
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "s")
        subprocess.run(["pdftoppm", "-png", "-scale-to", str(PX), "-singlefile", SRC.format(key), base], check=True)
        img = Image.open(base + ".png").convert("RGB")
    bg = img.getpixel((5, 5))
    d = ImageDraw.Draw(img)
    d.rectangle((0, BAND[0], PX, BAND[1]), fill=bg)
    en_col = tuple(round(0.7 * t + 0.3 * b) for t, b in zip(TEXT, bg))
    d.text((PX / 2, IS_BASE), icelandic, font=fitted(icelandic, round(76 * PT)), fill=TEXT, anchor="ms")
    d.text((PX / 2, EN_BASE), english, font=fitted(english, round(53 * PT)), fill=en_col, anchor="ms")
    img.save(OUT.format(key))
    print(key, icelandic, "/", english)


if __name__ == "__main__":
    for k, (a, b) in SIGNS.items():
        make(k, a, b)
