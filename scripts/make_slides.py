"""Marketing slide set (16:9, 1920x1080 PNG) from frames of the final walkthrough, in the thumbnail's style:
full-bleed render, dark gradient on the text side, FAB LAB SAGA eyebrow with a brand-colour cell, zone name in
Roboto Condensed, a brand-colour rule, the white logo bug bottom-right. Design and frame picks are Claude's;
zone names are Magnús's (same as the film titles; Rafeindaverkstæði from script v2 / the signs).
    /usr/bin/python3 scripts/make_slides.py        -> renders/slides/NN_<name>.png + FabLabSAGA_slides.pdf
"""
import os
import subprocess

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FR = os.path.join(ROOT, "renders/walk/final")
OUT = os.path.join(ROOT, "renders/slides")
FONTS = os.path.join(ROOT, "refs/branding/fonts")
TIT = os.path.join(ROOT, "renders/video_titles")
LOCK = os.path.expanduser("~/Documents/AgentWork/saga-video/fframes-title/media/lockup_white.png")
W, H = 1920, 1080
# brand colours (Fab Lab Ísland brand manual 2021)
RED, ORANGE, YELLOW, GREEN, BLUE, PINK = "#E03A3F", "#FFA13D", "#F2C200", "#009967", "#1245DE", "#E099AB"

# (file name, frame, kind, zone name, accent colour)
SLIDES = [
    ("01_forsida", 2300, "cover", None, None),
    ("02_yfirsyn", 540, "overview", None, RED),
    ("03_geislaskerar", 710, "zone", "Geislaskerar", RED),
    ("04_thrividdarprentarar", 860, "zone", "Þrívíddarprentarar", ORANGE),
    ("05_shopbot", 1100, "zone", "ShopBot Fræsir", YELLOW),
    ("06_rafeindaverkstaedi", 1420, "zone", "Rafeindaverkstæði", GREEN),
    ("07_textilsvaedi", 1650, "zone", "Textílsvæði", BLUE),
    ("08_vinnurymi", 1240, "zone", "Vinnurými", PINK),
    ("09_bunadarbanki", 1830, "zone", "Búnaðarbanki SFS", RED),
    ("10_setustofa", 2140, "image", None, None),
    ("11_samstarf", 2368, "partners", None, None),
]

f_eye = ImageFont.truetype(os.path.join(FONTS, "RobotoCondensed-Bold.ttf"), 34)
f_tag = ImageFont.truetype(os.path.join(FONTS, "RobotoCondensed-Regular.ttf"), 44)
f_zone = ImageFont.truetype(os.path.join(FONTS, "RobotoCondensed-Bold.ttf"), 132)
LK = Image.open(LOCK).convert("RGBA")


def lockup(width):
    return LK.resize((width, round(width * LK.height / LK.width)), Image.LANCZOS)


def gradient(mode, strength=225, reach=0.58, power=1.5):
    g = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(g)
    n = W if mode == "left" else H
    for i in range(n):
        p = i / (n * reach)
        if mode == "bottom":
            p = (n - 1 - i) / (n * reach)
        v = int(strength * max(0.0, 1 - p) ** power)
        if mode == "left":
            d.line([(i, 0), (i, H)], fill=v)
        else:
            d.line([(0, i), (W, i)], fill=v)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    sh.putalpha(g)
    return sh


def spaced(d, xy, text, font, spacing, fill="white"):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill, anchor="ls")
        x += font.getlength(ch) + spacing
    return x


def halo(layer, blur=10, strength=0.5):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * strength))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (2, 2))
    out.alpha_composite(layer)
    return out


def bug(im):
    b = lockup(200)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(b, (W - 65 - b.width, H - 65 - b.height))
    im.alpha_composite(halo(layer, 6, 0.45))


def eyebrow(d, x, base, colour):
    if colour:
        d.rectangle((x, base - 26, x + 26, base), fill=colour)
        x += 26 + 18
    spaced(d, (x, base), "FAB LAB SAGA", f_eye, 7)


def make(name, fno, kind, zone, colour):
    im = Image.open(os.path.join(FR, f"f{fno:05d}.png")).convert("RGBA")
    if kind == "cover":
        im = Image.alpha_composite(im, gradient("left"))
        lk = lockup(760)
        x, y = 110, (H - lk.height) // 2 - 50
        im.alpha_composite(lk, (x, y))
        ImageDraw.Draw(im).text((x + 14, y + lk.height + 40), "SKÖPUNAR- OG TÆKNISMIÐJA", font=f_tag,
                                fill="white", anchor="lt")
    elif kind == "zone":
        im = Image.alpha_composite(im, gradient("left", 215, 0.55))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x, base = 110, H - 250
        eyebrow(d, x, base - 160, colour)
        d.text((x - 6, base), zone, font=f_zone, fill="white", anchor="ls")
        d.rectangle((x, base + 40, x + 140, base + 48), fill=colour)
        im.alpha_composite(halo(layer, 12, 0.4))
        bug(im)
    elif kind == "overview":
        im = Image.alpha_composite(im, gradient("bottom", 200, 0.42))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        x, base = 110, H - 120
        eyebrow(d, x, base - 70, colour)
        spaced(d, (x, base), "SKÖPUNAR- OG TÆKNISMIÐJA", f_tag, 5)
        im.alpha_composite(halo(layer, 12, 0.4))
        bug(im)
    elif kind == "image":
        im = Image.alpha_composite(im, gradient("bottom", 150, 0.3))
        bug(im)
    elif kind == "partners":
        im = im.filter(ImageFilter.GaussianBlur(6))
        im = Image.alpha_composite(im, Image.new("RGBA", (W, H), (0, 0, 0, 205)))
        im.alpha_composite(Image.open(os.path.join(TIT, "outro.png")).convert("RGBA"))
    path = os.path.join(OUT, f"{name}.png")
    im.convert("RGB").save(path)
    return path


def main():
    os.makedirs(OUT, exist_ok=True)
    paths = [make(*s) for s in SLIDES]
    pdf = os.path.join(OUT, "FabLabSAGA_slides.pdf")
    subprocess.run(["magick", *paths, "-quality", "92", "-compress", "jpeg", "-density", "144", pdf], check=True)
    print("\n".join(paths + [pdf]))


if __name__ == "__main__":
    main()
