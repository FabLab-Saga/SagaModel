"""Generate the Fab Lab SAGA accent-wall mural as SVG (units: mm, origin top-left).

Wall: workshop face of the partition by the small rooms, 5240 x 3930 mm at
model y 21.82, seen from the benches looking -Y, so the viewer's left edge is
model x 29.50 and the right edge x 24.26 (svg_x = (29.50 - model_x) * 1000).
Shapes are laid out in model-x order (door 1780-2810 from x 24.26, column
3140-3540) and mirrored as a group into the viewer frame; in the viewer frame
the door is 2430-3460 (2660 high) and the column hides 1700-2100.

Visual language from the Fab Lab Ísland brand manual: chunky shapes on a square
grid built from squares, quarter circles and half discs, in the manual palette;
logo = Fab Lab icon + "FAB" bold / "LAB" light / "SAGA" light (Roboto Condensed).
Rule from the felt panels: never a lone raised rounded peak between lower shoulders.

Usage: python3 scripts/mural.py out.svg
"""
import sys
from pathlib import Path

W, H = 5240, 3930
DOOR_X0, DOOR_X1, DOOR_H = 1780, 2810, 2660
C = 655                                   # grid cell: 8 cells = full wall width
BAND = 2 * C                              # 1310; overlaps the door head by 40 mm (cut out)

RED, GREEN, BLUE = "#E03A3F", "#009967", "#1245DE"
ORANGE, YELLOW, PINK = "#FFA13D", "#F2C200", "#E099AB"
INK = "#000000"

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "refs/branding/fonts"
ICON = ROOT / "refs/branding/logos/fablab_icon.svg"


def square(x, y, col, n=1):
    return f'<rect x="{x}" y="{y}" width="{C * n}" height="{C}" fill="{col}"/>'


def quarter(x, y, col, corner):
    """Quarter disc filling one cell; `corner` is where the centre sits: tl, tr, bl, br."""
    cx = x + (C if corner in ("tr", "br") else 0)
    cy = y + (C if corner in ("bl", "br") else 0)
    sx = x if corner in ("tr", "br") else x + C
    ey = y if corner in ("bl", "br") else y + C
    sweep = {"tl": 1, "tr": 0, "bl": 0, "br": 1}[corner]
    return f'<path d="M{cx},{cy} L{sx},{cy} A{C},{C} 0 0 {sweep} {cx},{ey} Z" fill="{col}"/>'


def half_down(x, y, col):
    """Half disc hanging from the top edge of a 2x1 cell block (a 'bowl')."""
    return f'<path d="M{x},{y} A{C},{C} 0 0 0 {x + 2 * C},{y} Z" fill="{col}"/>'


def half_up(x, y, col):
    """Half disc standing on the bottom edge of a 2x1 block (an arch, always in a row of equals)."""
    return f'<path d="M{x},{y + C} A{C},{C} 0 0 1 {x + 2 * C},{y + C} Z" fill="{col}"/>'


def circle(x, y, col, r=None):
    r = r or C / 2
    return f'<circle cx="{x + C / 2}" cy="{y + C / 2}" r="{r}" fill="{col}"/>'


def door_portal():
    """Thick red arch ring framing the door: inner radius = half door width."""
    cx, cy = (DOOR_X0 + DOOR_X1) / 2, H - DOOR_H
    ri, ro = (DOOR_X1 - DOOR_X0) / 2, (DOOR_X1 - DOOR_X0) / 2 + 260
    return (f'<path d="M{cx - ro},{cy} A{ro},{ro} 0 0 1 {cx + ro},{cy} L{cx + ri},{cy} '
            f'A{ri},{ri} 0 0 0 {cx - ri},{cy} Z" fill="{RED}"/>'
            f'<rect x="{cx - ro}" y="{cy}" width="{ro - ri}" height="{DOOR_H}" fill="{RED}"/>'
            f'<rect x="{cx + ri}" y="{cy}" width="{ro - ri}" height="{DOOR_H}" fill="{RED}"/>')


def band():
    """Top band, row 0 (y 0) and row 1 (y C). The door portal sits in cols ~2-4 of row 1."""
    r0, r1 = 0, C
    s = []
    # row 0: a rhythm of bowls, quarters and squares across the full width
    s += [half_down(0, r0, BLUE), quarter(2 * C, r0, YELLOW, "tl"), square(3 * C, r0, PINK),
          quarter(4 * C, r0, GREEN, "tr"), half_down(5 * C, r0, ORANGE), quarter(7 * C, r0, BLUE, "tl")]
    # row 1: left of the portal and right of it (portal itself is drawn separately)
    s += [quarter(0, r1, PINK, "bl"), square(C, r1, GREEN), quarter(C, r1, YELLOW, "br")]
    s += [quarter(5 * C, r1, YELLOW, "bl"), circle(6 * C, r1, PINK), square(7 * C, r1, GREEN), quarter(7 * C, r1, ORANGE, "tl")]
    return s


def cascade():
    """Pieces stepping down the right-hand edge (right of the column), getting sparser."""
    x6, x7 = 6 * C, 7 * C                    # both fully right of the column (3140-3540)
    r2, r3, r4 = 2 * C, 3 * C, 4 * C
    return [square(x6, r2, RED), quarter(x7, r2, BLUE, "tr"),
            quarter(x6, r3, GREEN, "tr"), quarter(x7, r3, PINK, "bl"),
            circle(x7, r4, ORANGE, C * 0.42)]


def logo(x, y, icon_size=620):
    """Manual 'Version I': icon + three lines FAB (bold) / LAB / SAGA (light), tops aligned."""
    cap = icon_size * 0.46                     # proportions measured from fab_lab_island_logo.svg
    pitch = icon_size * 0.525
    fs = cap / 0.711                           # Roboto Condensed cap height = 0.711 em
    tx = x + icon_size * 1.10
    line = lambda i, fam, t: (f'<text x="{tx}" y="{y + cap + i * pitch}" font-family="{fam}" font-size="{fs}" '
                              f'letter-spacing="{-0.05 * fs}" fill="{INK}">{t}</text>')
    return (f'<image href="{ICON.as_uri()}" x="{x}" y="{y}" width="{icon_size}" height="{icon_size}"/>'
            + line(0, "RCB", "FAB") + line(1, "RCL", "LAB") + line(2, "RCL", "SAGA"))


def build():
    shapes = "".join(band() + cascade() + [door_portal()])
    vx0, vx1 = W - DOOR_X1, W - DOOR_X0          # door in the viewer frame
    fonts = (f'@font-face{{font-family:RCB;src:url("{(FONTS / "RobotoCondensed-Bold.ttf").as_uri()}")}}'
             f'@font-face{{font-family:RCL;src:url("{(FONTS / "RobotoCondensed-Light.ttf").as_uri()}")}}')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<style>{fonts}</style>'
            f'<clipPath id="wall"><path d="M0,0 H{W} V{H} H{vx1} V{H - DOOR_H} H{vx0} V{H} H0 Z"/></clipPath>'
            f'<rect width="{W}" height="{H}" fill="#EDEBE6"/>'
            f'<g clip-path="url(#wall)"><g transform="translate({W},0) scale(-1,1)">{shapes}</g>'
            f'{logo(vx1 + 260 + 120, 1640, 560)}</g></svg>')


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(build())
    print("wrote", sys.argv[1])
