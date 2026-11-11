"""Title graphics for the presentation video (brand manual pp. 56-57), as 1920x1080 transparent PNGs in
renders/video_titles/ (ffmpeg overlays them with fades in assemble_film.py).
    /usr/bin/python3 scripts/make_titles.py          (system python: Pillow; Inkscape Flatpak for the SVG logos)
- intro.png: FAB LAB SAGA lockup centred, white (on black in the film).
- outro.png: collaboration frame (variant B): lockup | thin vertical line | partner logos, all white.
- bug.png: small white lockup bottom-right (~168 px wide area, 65 px margins).
- title_<shot>.png: lower-left title, white, "FAB LAB SAGA // " Roboto Bold + name Roboto Light, ~63 px (47 pt),
  baseline aligned with the bug's first line. Shots and names from build_walkthrough.py.
The lockup is cut from refs/branding/Poster_FabLabSaga_A4.pdf (the project's own artwork), made white.
"""
import ast
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "renders/video_titles")
P = os.path.join(ROOT, "assets/partners")
FONTS = os.path.join(ROOT, "refs/branding/fonts")
W, H, M = 1920, 1080, 65
os.makedirs(OUT, exist_ok=True)


def lockup():
    """White FAB LAB SAGA lockup with alpha, cut from the poster PDF at 600 dpi."""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", "600", "-png", "-singlefile",
                        os.path.join(ROOT, "refs/branding/Poster_FabLabSaga_A4.pdf"), os.path.join(tmp, "p")], check=True)
        im = Image.open(os.path.join(tmp, "p.png")).convert("L")
    w, h = im.size
    c = im.crop((int(w * 0.52), int(h * 0.065), int(w * 0.93), int(h * 0.178)))
    a = ImageOps.invert(c).point(lambda v: 0 if v < 60 else min(255, int((v - 60) * 255 / 170)))   # drops a faint rule
    a = a.crop(a.getbbox())
    out = Image.new("RGBA", a.size, (255, 255, 255, 255))
    out.putalpha(a)
    return out


def svg_png(path, height):
    with tempfile.TemporaryDirectory(dir=os.path.expanduser("~/.hermes/cache/scratch")) as tmp:
        dst = os.path.join(tmp, "o.png")
        subprocess.run(["flatpak", "run", f"--filesystem={ROOT}", f"--filesystem={tmp}", "org.inkscape.Inkscape", path,
                        "--export-type=png", f"--export-filename={dst}", "-h", str(height)],
                       check=True, capture_output=True)
        im = Image.open(dst).convert("RGBA")
    return im.crop(im.getchannel("A").getbbox())


def fit_h(im, h):
    return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)


def white(im):
    out = Image.new("RGBA", im.size, (255, 255, 255, 255))
    out.putalpha(im.getchannel("A"))
    return out


def canvas():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def shadowed(im, blur=9, offset=2, strength=0.55):
    """Soft dark halo under white overlay art so it stays legible on light walls/floors (legibility aid only;
    the white artwork itself is unchanged)."""
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * strength))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(a)
    out = canvas()
    out.alpha_composite(sh, (offset, offset))
    out.alpha_composite(im)
    return out


def layer(im, xy):
    """Full-frame transparent layer with `im` placed at xy (for the fframes outro)."""
    out = canvas()
    out.alpha_composite(im, xy)
    return out


def main():
    LK = lockup()
    # intro
    im = canvas()
    lk = LK.resize((900, round(900 * LK.height / LK.width)), Image.LANCZOS)
    im.alpha_composite(lk, ((W - lk.width) // 2, (H - lk.height) // 2))
    im.save(os.path.join(OUT, "intro.png"))
    # bug (bottom-right)
    bug = LK.resize((200, round(200 * LK.height / LK.width)), Image.LANCZOS)
    bx, by = W - M - bug.width, H - M - bug.height
    im = canvas()
    im.alpha_composite(bug, (bx, by))
    shadowed(im, blur=6, strength=0.45).save(os.path.join(OUT, "bug.png"))
    # titles: baseline on the bug's first text line (FAB LAB occupies ~the upper half of the lockup)
    base = by + round(bug.height * 0.47)
    fb = ImageFont.truetype(os.path.join(FONTS, "Roboto-Bold.ttf"), 63)
    fl = ImageFont.truetype(os.path.join(FONTS, "Roboto-Light.ttf"), 63)
    src = ast.parse(open(os.path.join(ROOT, "scripts/build_walkthrough.py")).read())
    shots = next(ast.literal_eval(t.value) for t in src.body if isinstance(t, ast.Assign)
                 and getattr(t.targets[0], "id", "") == "SHOTS")
    for name, _bars, title, *_ in shots:
        if not title:
            continue
        im = canvas()
        d = ImageDraw.Draw(im)
        pre, sep, nm = title.rpartition("// ")
        x = M
        if sep:
            d.text((x, base), pre + sep, font=fb, fill="white", anchor="ls")
            x += round(fb.getlength(pre + sep))
        d.text((x, base), nm, font=fl, fill="white", anchor="ls")
        shadowed(im).save(os.path.join(OUT, f"title_{name}.png"))
    # outro, variant B: lockup | line | partners (2 x 2), all white
    im = canvas()
    lk = LK.resize((560, round(560 * LK.height / LK.width)), Image.LANCZOS)
    parts = [white(svg_png(os.path.join(P, "HI_Verkfraedi-og-natturuvisindasvid_IS_white.svg"), 300)),
             # NýMennt á Menntavísindasviði replaces the plain Menntavísindasvið identifier (2026-11-11)
             white(Image.open(os.path.join(P, "HI_NyMennt_IS_white_derived.png")).convert("RGBA")),
             white(svg_png(os.path.join(P, "Reykjavik_logo_white.svg"), 300)),
             white(Image.open(os.path.join(P, "Mixtura_wordmark_white_derived-crop.png")).convert("RGBA"))]
    heights = [72, 96, 104, 78]      # NýMennt taller than the school identifier: its sub-line is unreadable at 72
    parts = [fit_h(p, h) for p, h in zip(parts, heights)]
    for i, p in enumerate(parts):                                    # keep every partner logo <= 760 px wide
        if p.width > 760:
            parts[i] = p.resize((760, round(p.height * 760 / p.width)), Image.LANCZOS)
    gap, col_w = 56, max(p.width for p in parts)
    block_h = sum(p.height for p in parts) + gap * 3
    total_w = lk.width + 2 * 80 + 2 + col_w
    x0 = (W - total_w) // 2
    cy = H // 2
    im.alpha_composite(lk, (x0, cy - lk.height // 2))
    lx = x0 + lk.width + 80
    ImageDraw.Draw(im).rectangle((lx, cy - block_h // 2, lx + 1, cy + block_h // 2), fill="white")
    y = cy - block_h // 2
    # the same frame as separate full-frame layers, animated by the fframes outro card
    LAY = os.path.join(OUT, "outro_layers")
    os.makedirs(LAY, exist_ok=True)
    layer(lk, (x0, cy - lk.height // 2)).save(os.path.join(LAY, "outro_lockup.png"))
    for i, p in enumerate(parts):
        im.alpha_composite(p, (lx + 82, y))
        layer(p, (lx + 82, y)).save(os.path.join(LAY, f"outro_partner{i}.png"))
        y += p.height + gap
    with open(os.path.join(LAY, "geometry.txt"), "w") as fh:     # divider line for the fframes card
        fh.write(f"line_x={lx} line_top={cy - block_h // 2} line_bottom={cy + block_h // 2} lockup_x={x0} "
                 f"lockup_w={lk.width} lockup_y={cy - lk.height // 2} lockup_h={lk.height}\n")
    im.save(os.path.join(OUT, "outro.png"))
    print("titles written to", OUT)


if __name__ == "__main__":
    main()
