"""Búnaðarbankinn (equipment bank) and the lounge/entryway. Re-runnable.

Equipment bank = the enclosure at the ESE end (model frame: +X = SSW, +Y = ESE):
  Boxes only - no machinery in the bank (user, 2026-10-07).
  A  back-wall run, y 37.73-38.33, 60 cm deep, x 21.05 -> ~32.4: large-box bays.
  B  south-wall run, y 34.42-34.82, 40 cm deep: small boxes, full height.
  C  NNE end, x 21.05-21.65, 60 cm deep: biggest boxes (C0 = corner unit y 34.40-35.65 next to run B).
  Contents: IKEA SAMLA-style clear boxes (5-130 L) full of random teaching kit.
Lounge: one small CIRCULAR conversation nook by the SSW glass (centre 30.95, 31.6; 2.85 m across): a 240-degree
  curved sofa (charcoal linen, back to the glass, open towards the path by the spine), felt cushions, a round
  birch table, two felt poufs at the opening. Walkways kept clear: 1.3 m between nook and spine, the entrance
  zone (y > 34.3) and the strip along the glass from the laser room.
Placeholders inside these areas are hidden, not deleted.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_src = open(HERE + "build_machines.py").read()
mach = {}
exec(_src[:_src.index("def build():")], mach)          # machine models only, no build
mach["materials"]()
M = mach["M"]
Part = lib["Part"]
mat = lib["simple_mat"]
lin = lib["lin"]
rng = random.Random(7)


# ---------------------------------------------------------------- materials
def clear_plastic(name, tint, opacity):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    gl = nt.nodes.new("ShaderNodeBsdfPrincipled")
    gl.inputs["Base Color"].default_value = lin(tint)
    gl.inputs["Roughness"].default_value = 0.18
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.95, 0.97, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 1.0 - opacity
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(gl.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*lin(tint)[:3], 0.3)
    m.surface_render_method = "BLENDED"
    return m


def fabric(name, hexcol):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Sheen Weight"].default_value = 0.7
    if not any(n.type == "TEX_NOISE" for n in nt.nodes):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 700
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.15
        nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = lin(hexcol)
    return m


SAMLA = clear_plastic("SAMLA_Clear", "#DDE6EA", 0.32)
LID = clear_plastic("SAMLA_Lid", "#CFE0EA", 0.45)
WHITE_BOX = mat("Box_White", "#F1F0EC", 0.4)
LABEL = mat("Label_Paper", "#FAFAF7", 0.7)
STEEL = mat("Cart_Black", "#1F1F20", 0.45, metal=0.3)
SOFA = fabric("Sofa_LightGrey", "#C2C2BD")
RUG = fabric("Rug_Grey", "#8D8B86")
SCREEN = mat("TV_Screen", "#0B0C0E", 0.08, coat=0.8)
STUFF = MAT["bins"] + [mat("Stuff_White", "#EDEDEA", 0.4), mat("Stuff_Black", "#1A1A1A", 0.35),
                       mat("Stuff_Grey", "#7C8085", 0.4), mat("Stuff_Teal", "#2FA4A0", 0.4)]

# SAMLA sizes (w, d, h), litres as name
SIZES = {5: (0.28, 0.20, 0.14), 11: (0.39, 0.28, 0.14), 22: (0.39, 0.28, 0.28),
         45: (0.57, 0.39, 0.28), 65: (0.57, 0.39, 0.42), 130: (0.79, 0.57, 0.43)}


# ---------------------------------------------------------------- boxes
def samla(part, x, y, z, size, white=False):
    """Box with lid and label in the part's local frame; front face at y."""
    w, d, h = SIZES[size]
    body = WHITE_BOX if white else SAMLA
    t = 0.004
    part.box(body, x, x + w, y, y + d, z, z + t)                        # floor
    part.box(body, x, x + w, y, y + t, z, z + h - 0.02)                 # front
    part.box(body, x, x + w, y + d - t, y + d, z, z + h - 0.02)
    part.box(body, x, x + t, y, y + d, z, z + h - 0.02)
    part.box(body, x + w - t, x + w, y, y + d, z, z + h - 0.02)
    part.box(LID, x - 0.006, x + w + 0.006, y - 0.006, y + d + 0.006, z + h - 0.02, z + h, bevel=0.004)
    part.box(LABEL, x + w * 0.3, x + w * 0.7, y - 0.002, y, z + h * 0.45, z + h * 0.62)
    if not white:                                                        # random kit inside
        fill = rng.uniform(0.45, 0.85) * (h - 0.03)
        cx = x + 0.015
        while cx < x + w - 0.05:
            cw = rng.uniform(0.04, min(0.18, x + w - 0.015 - cx))
            for row in range(2):
                ch = fill * rng.uniform(0.5, 1.0)
                cy0 = y + 0.015 + row * (d - 0.03) / 2
                part.box(rng.choice(STUFF), cx, cx + cw * 0.92, cy0, cy0 + (d - 0.03) / 2 * 0.9, z + t, z + t + ch, bevel=0.003)
            cx += cw


def fill_shelf(part, x0, x1, depth, z, clear_h, big=True):
    """Fill one shelf front-to-back with random SAMLA boxes that fit."""
    fits = [s for s, (w, d, h) in SIZES.items() if d <= depth - 0.01 and h <= clear_h - 0.02 and (big or s <= 22)]
    if not fits:
        return
    x = x0 + 0.012
    while True:
        cand = [s for s in fits if x + SIZES[s][0] <= x1 - 0.012]
        if not cand:
            break
        s = rng.choice(cand)
        w, d, h = SIZES[s]
        white = rng.random() < 0.12
        samla(part, x, 0.012, z, s, white)
        if 2 * h + 0.01 <= clear_h - 0.02 and rng.random() < 0.6:     # stack a second box
            on_top = [q for q in cand if SIZES[q][0] <= w and SIZES[q][1] <= d and SIZES[q][2] <= clear_h - 0.03 - h]
            if not on_top:
                x += w + rng.uniform(0.01, 0.04)
                continue
            s2 = rng.choice(on_top)
            samla(part, x + (w - SIZES[s2][0]) / 2, 0.012 + (d - SIZES[s2][1]) / 2, z + h + 0.002, s2, rng.random() < 0.12)
        x += w + rng.uniform(0.01, 0.04)


def fill_unit(slots, levels, height, depth, big=True, skip=()):
    part = Part()
    tops = list(levels) + [height]
    for (bi, li), (xa, xb, _, _, zt) in slots.items():
        if (bi, li) in skip:
            continue
        clear = tops[li + 1] - zt - 0.06                                 # minus next board + its rail
        fill_shelf(part, xa, xb, depth, zt, clear, big)
    return part


# ---------------------------------------------------------------- carts
def bekant(w):
    """IKEA Bekant storage on castors (w x 0.46 x 1.03): black steel mesh carcass, birch drawer."""
    p = Part()
    d, h = 0.46, 1.03
    for x in (0.0, w - 0.02):
        for y in (0.0, d - 0.02):
            p.box(STEEL, x, x + 0.02, y, y + 0.02, 0.07, h)
            p.cyl(MAT["foot"], (x + 0.01, y + 0.01, 0.0), (x + 0.01, y + 0.01, 0.05), 0.025, seg=14)
    for z in (0.07, 0.45, h - 0.02):
        p.box(STEEL, 0, w, 0, d, z, z + 0.02)
    p.box(STEEL, 0, w, d - 0.005, d, 0.07, h)                            # back
    for x in (0.0, w - 0.003):
        p.box(STEEL, x, x + 0.003, 0, d, 0.07, h)                        # sides
    p.box(MAT["ply"], 0.02, w - 0.02, -0.005, d - 0.02, h - 0.24, h - 0.03, bevel=0.003)   # birch drawer
    p.box(STEEL, w * 0.35, w * 0.65, -0.015, -0.005, h - 0.12, h - 0.10)                    # handle
    return p


def bror(w=0.85, d=0.55, h=0.88):
    p = Part()
    for x in (0.0, w - 0.03):
        for y in (0.0, d - 0.03):
            p.box(STEEL, x, x + 0.03, y, y + 0.03, 0.08, h)
            p.cyl(MAT["foot"], (x + 0.015, y + 0.015, 0.0), (x + 0.015, y + 0.015, 0.06), 0.03, seg=14)
    for z in (0.12, h - 0.03):
        p.box(STEEL, 0, w, 0, d, z, z + 0.03, bevel=0.003)
    return p


# ---------------------------------------------------------------- lounge pieces
def sofa(L, d=0.86, h=0.81, m=None):
    """Cleveland-style sofa: plinth on short legs, seat + back cushions, square arms."""
    SOFA = m or globals()["SOFA"]
    p = Part()
    arm = 0.16
    for x in (0.06, L - 0.10):
        for y in (0.06, d - 0.10):
            p.box(MAT["foot"], x, x + 0.04, y, y + 0.04, 0.0, 0.10)
    p.box(SOFA, 0, L, 0, d, 0.10, 0.30, bevel=0.02)                       # base
    p.box(SOFA, 0, arm, 0, d, 0.10, 0.62, bevel=0.04)                     # arms
    p.box(SOFA, L - arm, L, 0, d, 0.10, 0.62, bevel=0.04)
    p.box(SOFA, arm, L - arm, d - 0.20, d, 0.30, h, bevel=0.05)          # back
    n = 3 if L > 2.0 else 2
    cw = (L - 2 * arm) / n
    for i in range(n):
        x = arm + i * cw
        p.box(SOFA, x + 0.006, x + cw - 0.006, 0.0, d - 0.20, 0.30, 0.44, bevel=0.04)      # seat cushions
        p.box(SOFA, x + 0.01, x + cw - 0.01, d - 0.36, d - 0.18, 0.44, h - 0.03, bevel=0.06)  # back cushions
    return p


def pouf(m, r=0.23, h=0.42):
    p = Part()
    p.cyl(m, (r, r, 0.0), (r, r, h - 0.04), r, seg=40)
    bmesh.ops.create_uvsphere(p.bm(m), u_segments=40, v_segments=10, radius=r,
                              matrix=Matrix.Translation((r, r, h - 0.04)) @ Matrix.Scale(0.18, 4, (0, 0, 1)))
    return p


def tv_stand(sw=1.92, sh=1.10):
    p = Part()
    w, d = 1.10, 0.62
    p.box(STEEL, 0.05, w - 0.05, 0.10, d - 0.10, 0.08, 0.12)                # base
    for x in (0.0, w - 0.06):
        p.box(STEEL, x, x + 0.06, d / 2 - 0.25, d / 2 + 0.25, 0.04, 0.08)   # feet
    p.box(STEEL, w / 2 - 0.05, w / 2 + 0.05, d / 2 - 0.03, d / 2 + 0.03, 0.12, 1.55)  # column
    x0 = w / 2 - sw / 2
    p.box(STEEL, x0, x0 + sw, d / 2 - 0.08, d / 2 - 0.03, 0.80, 0.80 + sh, bevel=0.005)
    p.box(SCREEN, x0 + 0.01, x0 + sw - 0.01, d / 2 - 0.082, d / 2 - 0.08, 0.81, 0.80 + sh - 0.01)
    return p


def sector(p, m, c, r0, r1, a0, a1, z0, z1, n=10):
    """Closed annular-sector solid around centre c (angles in radians)."""
    bm = p.bm(m)
    rings = []
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((c.x + r * ca, c.y + r * sa, z)) for r, z in ((r0, z0), (r1, z0), (r1, z1), (r0, z1))])
    for q0, q1 in zip(rings, rings[1:]):
        for k in range(4):
            bm.faces.new((q0[k], q0[(k + 1) % 4], q1[(k + 1) % 4], q1[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def soften(root, names, width=0.03):
    for k in root.children:
        if any(k.name.endswith(n) for n in names):
            bv = k.modifiers.new("Soft", "BEVEL")
            bv.width, bv.segments, bv.limit_method = width, 3, "ANGLE"
            sd = k.modifiers.new("Subd", "SUBSURF")
            sd.levels, sd.render_levels = 1, 2
            for f in k.data.polygons:
                f.use_smooth = True


def gullvalla(fab, leg, cushion=None, cushion_left=True):
    """IKEA GULLVALLA 2-seat sofa, Silkeryd grey-green (142 x 83 x 78 incl. back cushions, backrest 70, seat height
    42, seat depth 48, seat width 120, free height under 15; modelled from the IKEA product photos): softly rolled
    arms that sweep down a little towards the front, two seat cushions, two plump loose back cushions leaning back,
    black stepped/turned tapered legs. Local frame: x = width, front at y = 0, back at y = 0.83."""
    W, D, SH = 1.42, 0.83, 0.42
    p = Part()
    zl, aw = 0.15, 0.11                                               # underside of the body, arm thickness
    p.box(fab, aw - 0.01, W - aw + 0.01, 0.02, D - 0.02, zl, SH - 0.10, bevel=0.03)              # base frame
    for i in range(2):                                                # two seat cushions
        x0 = aw + i * (W - 2 * aw) / 2
        p.box(fab, x0 + 0.004, x0 + (W - 2 * aw) / 2 - 0.004, 0.0, D - 0.16, SH - 0.10, SH, bevel=0.035)
    p.box(fab, aw - 0.01, W - aw + 0.01, D - 0.16, D, zl, 0.70, bevel=0.05)                      # back frame
    for i in range(2):                                                # two loose back cushions, leaning back
        cx = aw + (i + 0.5) * (W - 2 * aw) / 2
        mtx = Matrix.Translation((cx, D - 0.26, SH + 0.18)) @ Matrix.Rotation(math.radians(-11), 4, "X") \
            @ Matrix.Diagonal(((W - 2 * aw) / 2 - 0.02, 0.19, 0.38, 1))
        bmesh.ops.create_cube(p.bm(fab), size=1.0, matrix=mtx)
    # rolled arms: one solid arm each + a rolled top (cylinder along the depth), front of the roll set back a little
    for x0 in (0.0, W - aw):
        p.box(fab, x0, x0 + aw, 0.01, D, zl, 0.57, bevel=0.03)
        p.cyl(fab, (x0 + aw / 2, 0.02, 0.575), (x0 + aw / 2, D, 0.585), aw / 2 + 0.008, seg=24)
    # black stepped, turned legs
    for x in (0.06, W - 0.06):
        for y in (0.07, D - 0.07):
            for z0, z1, r0, r1 in ((0.0, 0.07, 0.016, 0.019), (0.07, 0.075, 0.021, 0.021), (0.075, 0.13, 0.020, 0.023),
                                   (0.13, 0.15, 0.026, 0.026)):
                bmesh.ops.create_cone(p.bm(leg), cap_ends=True, segments=20, radius1=r0, radius2=r1, depth=z1 - z0,
                                      matrix=Matrix.Translation((x, y, (z0 + z1) / 2)))
    if cushion is not None:                                          # one loose felt cushion
        cxx = aw + 0.24 if cushion_left else W - aw - 0.24
        mtx = Matrix.Translation((cxx, D - 0.40, SH + 0.16)) @ Matrix.Rotation(math.radians(-16), 4, "X") \
            @ Matrix.Diagonal((0.40, 0.11, 0.36, 1))
        bmesh.ops.create_cube(p.bm(cushion), size=1.0, matrix=mtx)
    return p, W, D


def conversation_pit(col):
    """Lounge by the SSW glass (user choice 2026-10-08): two straight 2-seat sofas FACING EACH OTHER across a low
    birch coffee table, set at right angles to the glass so both sides get the window light, two felt poufs closing
    the open (lab-side) end; the glass closes the other end - people sit in a ring of 6 and face each other.
    Sofas = IKEA GULLVALLA 2-seat, Silkeryd grey-green (142 x 83 x 78, user choice), table 1.00 x 0.55 x 0.40.
    Pushed against the glass (x 30.39-32.40, y 30.11-33.29) so the route from the entrance into the lab stays open:
    >= 1.2 m between the on-call desk corner (29.92, 33.87) and the pit, ~2 m between pit and spine further on."""
    char = bpy.data.materials.get("Sofa_Charcoal")
    if char is None:
        char = SOFA.copy()
        char.name = "Sofa_Charcoal"
        mix = next((n for n in char.node_tree.nodes if n.type == "MIX"), None)
        if mix:
            mix.inputs["B"].default_value = lin("#2A2D30")
            mix.inputs["Factor"].default_value = 0.9
        char.diffuse_color = lin("#3E4144")
        bsdf = next(n for n in char.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        bsdf.inputs["Sheen Weight"].default_value = 0.3
        bsdf.inputs["Sheen Tint"].default_value = (0.35, 0.36, 0.38, 1)
    felts = [bpy.data.materials[n] for n in ("Floff_Orange", "Floff_Green", "Floff_Blue")]
    green = fabric("Silkeryd_GreyGreen", "#3E5530")                   # GULLVALLA, Silkeryd grey-green
    gb = next(n for n in green.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    gb.inputs["Sheen Weight"].default_value = 0.25                   # strong white sheen washed the green out
    gb.inputs["Sheen Tint"].default_value = (0.45, 0.55, 0.40, 1)
    leg = mat("Leg_BlackStained", "#141414", 0.45)
    X1, CY = 32.40, 31.70                                            # glass end, pit axis
    L = 1.42
    X0 = X1 - L
    for k, (y_front, facing) in enumerate(((30.94, "+y"), (32.46, "-y"))):
        p, L, D = gullvalla(green, leg, felts[(k * 2) % 3], cushion_left=bool(k))
        cy = y_front - D / 2 if facing == "+y" else y_front + D / 2
        loc, rot = lib["placement"](X0 + L / 2, cy, L, D, facing)
        root = p.emit(f"Lounge_Sofa_{k + 1}", col, loc, rot)
        soften(root, ("Silkeryd_GreyGreen",) + tuple(f.name for f in felts), 0.025)
    t = Part()                                                           # low birch coffee table, profile frame
    TL, TD, TH = 1.00, 0.55, 0.40
    tx0, ty0 = X0 + L / 2 - TL / 2, CY - TD / 2
    for x in (tx0, tx0 + TL - 0.04):
        for y in (ty0, ty0 + TD - 0.04):
            t.profile(0.04, "z", x, y, 0.0, TH - 0.025)
    for y in (ty0, ty0 + TD - 0.04):
        t.profile(0.04, "x", tx0 + 0.04, y, TH - 0.065, TL - 0.08)
    t.box(MAT["ply"], tx0 + 0.04, tx0 + TL - 0.04, ty0 + 0.02, ty0 + TD - 0.02, 0.10, 0.118)            # magazine shelf
    t.box(MAT["ply"], tx0 - 0.01, tx0 + TL + 0.01, ty0 - 0.01, ty0 + TD + 0.01, TH - 0.025, TH, bevel=0.003)
    # what's on it: a sketchbook, a 3D print, two mugs, a demo piece being passed round
    t.box(mat("Sketchbook", "#F2F0EA", 0.8), tx0 + 0.15, tx0 + 0.45, ty0 + 0.12, ty0 + 0.33, TH, TH + 0.012)
    t.cyl(STUFF[3], (tx0 + 0.75, ty0 + 0.30, TH), (tx0 + 0.75, ty0 + 0.30, TH + 0.10), 0.035, seg=24)
    for dx, dy in ((0.95, 0.15), (0.35, 0.47)):
        t.cyl(mat("Mug_White", "#F4F3EF", 0.3, coat=0.3), (tx0 + dx, ty0 + dy, TH), (tx0 + dx, ty0 + dy, TH + 0.09), 0.04, seg=24)
    t.emit("Lounge_Table", col, Vector((0, 0, 0)))
    for k, dy in enumerate((-0.33, 0.33)):                               # two poufs close the open (lab) end
        pouf(felts[(k + 1) % 3]).emit(f"Pouf_{k + 1}", col, Vector((30.62 - 0.23, CY + dy - 0.23, 0)))


def nook(col, c, R=1.42, opening=math.radians(190), arc=math.radians(240)):
    """Circular conversation nook: 240-degree curved sofa (6 modules), round birch table, felt cushions, 2 poufs."""
    char = bpy.data.materials.get("Sofa_Charcoal")
    if char is None:
        char = SOFA.copy()
        char.name = "Sofa_Charcoal"
    mix = next((n for n in char.node_tree.nodes if n.type == "MIX"), None)
    if mix:
        mix.inputs["B"].default_value = lin("#2A2D30")
        mix.inputs["Factor"].default_value = 0.9
    char.diffuse_color = lin("#3E4144")
    bsdf = next(n for n in char.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Sheen Weight"].default_value = 0.3                     # white sheen washes out a dark fabric
    bsdf.inputs["Sheen Tint"].default_value = (0.35, 0.36, 0.38, 1)
    felts = [bpy.data.materials[n] for n in ("Floff_Orange", "Floff_Green", "Floff_Blue")]
    a_start = opening + (2 * math.pi - arc) / 2
    mods, g = 6, math.radians(0.8)
    step = arc / mods
    p = Part()
    sector(p, MAT["foot"], c, 0.80, R - 0.08, a_start, a_start + arc, 0.0, 0.10, n=48)            # recessed plinth
    for i in range(mods):
        a0, a1 = a_start + i * step + g, a_start + (i + 1) * step - g
        sector(p, char, c, 0.74, R, a0, a1, 0.10, 0.28, n=8)                                      # base
        sector(p, char, c, 0.72, R - 0.20, a0, a1, 0.28, 0.44, n=8)                               # seat cushion
        sector(p, char, c, R - 0.20, R, a0, a1, 0.28, 0.80, n=8)                                  # back
    for k, i in enumerate((0.9, 2.6, 4.3)):                                                       # loose felt cushions
        a = a_start + i * step
        ctr = c + Vector((math.cos(a), math.sin(a), 0)) * (R - 0.30) + Vector((0, 0, 0.62))
        mtx = Matrix.Translation(ctr) @ Matrix.Rotation(a + math.pi / 2, 4, "Z") @ Matrix.Rotation(math.radians(-14), 4, "X") \
            @ Matrix.Diagonal((0.42, 0.11, 0.38, 1))
        bmesh.ops.create_cube(p.bm(felts[k]), size=1.0, matrix=mtx)
    root = p.emit("Nook_Sofa", col, Vector((0, 0, 0)))
    soften(root, ("Sofa_Charcoal",) + tuple(f.name for f in felts), 0.035)
    t = Part()                                                                                    # round birch table
    t.cyl(MAT["ply"], (c.x, c.y, 0.375), (c.x, c.y, 0.40), 0.36, seg=64)
    for a in (0.0, math.pi / 2):
        d = Vector((math.cos(a), math.sin(a), 0)) * 0.26
        t.box(MAT["profile"], min(c.x - d.x, c.x + d.x) - 0.02, max(c.x - d.x, c.x + d.x) + 0.02,
              min(c.y - d.y, c.y + d.y) - 0.02, max(c.y - d.y, c.y + d.y) + 0.02, 0.02, 0.06)
    t.box(MAT["profile"], c.x - 0.02, c.x + 0.02, c.y - 0.02, c.y + 0.02, 0.06, 0.375)
    t.emit("Nook_Table", col, Vector((0, 0, 0)))
    for k, da in enumerate((-0.42, 0.42)):                                                        # poufs at the opening
        a = opening + da
        q = c + Vector((math.cos(a), math.sin(a), 0)) * 1.08
        pouf(felts[(k + 1) % 3]).emit(f"Pouf_{k + 1}", col, Vector((q.x - 0.23, q.y - 0.23, 0)))


# ---------------------------------------------------------------- build
def clear_collection(name):
    scene = bpy.context.scene
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if data is not None and data.users == 0:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)                       # lights are kept (re-used by name)
    return col


def hide_placeholders(x0, x1, y0, y1, keep):
    n = 0
    for o in bpy.data.objects["ROOT"].children:
        if o.name in keep or o.name.startswith(("ROOT", "Saga_Fablab", "glass door", "WINDOW", "osb st2")):
            continue
        pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" for c in k.bound_box]
        if pts and x0 <= min(p.x for p in pts) and max(p.x for p in pts) <= x1 and y0 <= min(p.y for p in pts) and max(p.y for p in pts) <= y1:
            for k in (o, *o.children_recursive):
                k.hide_render = k.hide_viewport = True
            n += 1
    return n


def put(part, name, col, loc, rot, local_xy, z, w, d):
    c = lib["to_world"](loc, rot, (local_xy[0], local_xy[1], 0))
    off = Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0))
    return part.emit(name, col, Vector((c.x, c.y, z)) + off, rot)


def desk_niche(slot, loc, rot, col):
    """Props on the standing-desk board of the A1 niche (local frame of the shelf run, front = y 0)."""
    xa, xb, _, _, zt = slot
    p = Part()
    grey = mat("LabelPrinter", "#2B2D30", 0.4)
    samla(p, xa + 0.05, 0.10, zt, 22)                                  # box being sorted
    p.box(grey, xa + 0.48, xa + 0.64, 0.30, 0.47, zt, zt + 0.09, bevel=0.01)          # label printer
    p.box(mat("Label_Tape", "#F2F1EC", 0.6), xa + 0.50, xa + 0.62, 0.27, 0.30, zt + 0.04, zt + 0.041)
    lap = bpy.data.materials.get("Laptop_Body") or grey
    p.box(lap, xa + 0.75, xa + 1.07, 0.08, 0.30, zt, zt + 0.012, bevel=0.003)         # laptop, open
    p.box(lap, xa + 0.75, xa + 1.07, 0.30, 0.305, zt + 0.012, zt + 0.23, bevel=0.002)
    p.box(mat("Tray_Grey", "#7C8085", 0.5), xa + 0.47, xa + 0.72, 0.06, 0.24, zt, zt + 0.03, bevel=0.003)
    for k in range(4):
        x = xa + 1.10 + (k % 2) * 0.06
        p.box(MAT["bins"][k], x, x + 0.05, 0.08 + (k // 2) * 0.09, 0.15 + (k // 2) * 0.09, zt, zt + 0.02, bevel=0.002)
    p.box(MAT["ply"], xa + 0.02, xb - 0.02, 0.585, 0.60, zt, zt + 0.48)               # ply back panel in the niche
    p.emit("Bank_DeskNiche", col, loc, rot)


def build():
    bank = clear_collection("EquipmentBank")
    lounge = clear_collection("Lounge")
    hidden = hide_placeholders(20.9, 32.45, 35.15, 38.40, keep=())

    H = 2.42
    # A1: large-box bays at the NNE end of the back wall
    lv_a1 = [0.12, 0.56, 0.95, 1.44, 1.88]
    DESK = {(1, 0), (1, 1), (1, 3)}                                    # middle bay = standing desk niche (board at 0.95)
    part, slots, L1 = lib["shelf_unit"]([1.25, 1.25, 1.25], 0.60, H, lv_a1, omit=DESK)
    loc, rot = lib["placement"](21.05 + L1 / 2, 38.33 - 0.30, L1, 0.60, "-y")
    part.emit("Bank_A1_Shelving", bank, loc, rot)
    fill_unit(slots, lv_a1, H, 0.60, skip=DESK | {(1, 2)}).emit("Bank_A1_Boxes", bank, loc, rot)
    desk_niche(slots[(1, 2)], loc, rot, bank)
    # A2: more box bays along the rest of the back wall (no machinery in the bank - boxes only)
    bays = [1.20] * 6
    lv_a2 = lv_a1
    part, slots2, L2 = lib["shelf_unit"](bays, 0.60, H, lv_a2)
    x2 = 21.05 + L1 + 0.005
    loc2, rot2 = lib["placement"](x2 + L2 / 2, 38.33 - 0.30, L2, 0.60, "-y")
    part.emit("Bank_A2_Shelving", bank, loc2, rot2)
    DEMO = {2, 3, 4, 5}                                                 # bays visible from the entrance: demo pieces
    fill_unit(slots2, lv_a2, H, 0.60, skip={k for k in slots2 if k[0] in DEMO}).emit("Bank_A2_Boxes", bank, loc2, rot2)
    demo = {}
    exec(open(HERE + "build_demo.py").read(), demo)
    print("demo pieces:", demo["demo_fill"](lib, slots2, lv_a2, H, 0.60, loc2, rot2, lounge, DEMO))
    # B: small boxes against the OSB wall, facing +y
    lv_b = [0.10, 0.48, 0.86, 1.24, 1.62, 2.00]
    part, slots_b, Lb = lib["shelf_unit"]([1.11] * 5, 0.40, H, lv_b)
    loc_b, rot_b = lib["placement"](21.66 + Lb / 2, 34.42 + 0.20, Lb, 0.40, "+y")         # against the moved south wall
    part.emit("Bank_B_SmallBoxShelving", bank, loc_b, rot_b)
    fill_unit(slots_b, lv_b, H, 0.40, big=False).emit("Bank_B_Boxes", bank, loc_b, rot_b)
    # C: NNE end, facing +x: biggest boxes + sewing machines
    lv_c = [0.12, 0.62, 1.12, 1.62, 2.02]
    part, slots_c, Lc = lib["shelf_unit"]([0.95, 0.95], 0.60, H, lv_c)
    loc_c, rot_c = lib["placement"](21.05 + 0.30, 35.66 + Lc / 2, Lc, 0.60, "+x")
    part.emit("Bank_C_Shelving", bank, loc_c, rot_c)
    fill_unit(slots_c, lv_c, H, 0.60).emit("Bank_C_Boxes", bank, loc_c, rot_c)
    # packing table in the middle: standing height, no stools. Clear floor between shelf fronts is
    # x 21.64-27.49, y 34.81-37.74 (2.93 m). Sized so >= 1.1 m stays free in front of every shelf run (a large
    # adult crouching behind a huge box pulled off a bottom shelf: box ~0.6 m + person ~0.5 m) and 1.2 m by the
    # secret door: 3.0 x 0.70 m centred at (24.50, 36.275) -> 1.12 m to runs A and B, 1.36 m to C, 1.49 m to the door.
    TL, TD, TH = 3.00, 0.70, 0.92
    part, _ = lib["table_unit"](TL, TD, TH, [0.0, TL / 2 - 0.02, TL - 0.04], lower=(0.15,))
    tloc, trot = lib["placement"](24.50, 36.275, TL, TD, "-y")
    part.emit("Bank_PackingTable", bank, tloc, trot)
    pk = Part()
    cb = bpy.data.materials.get("Cardboard") or mat("Cardboard", "#B08A5B", 0.85)
    pk.box(cb, 0.35, 0.80, 0.18, 0.52, TH, TH + 0.30, bevel=0.004)                     # open shipping box
    pk.box(cb, 0.33, 0.82, 0.16, 0.18, TH + 0.30, TH + 0.42)                           # flap
    pk.box(M["black"], 1.20, 1.36, 0.28, 0.36, TH, TH + 0.09, bevel=0.01)              # tape dispenser
    pk.cyl(mat("Tape_Clear", "#C9B98A", 0.3), (1.25, 0.32, TH + 0.10), (1.31, 0.32, TH + 0.10), 0.045, seg=20)
    pk.box(mat("Label_Printer", "#2B2C2E", 0.4), 1.75, 1.92, 0.22, 0.40, TH, TH + 0.08, bevel=0.01)
    pk.box(mat("Label_Roll", "#F4F2EC", 0.6), 1.92, 1.95, 0.27, 0.35, TH + 0.01, TH + 0.05)
    pk.box(MAT["bins"][1], 2.30, 2.70, 0.15, 0.45, TH, TH + 0.12, bevel=0.004)          # returns tray
    pk.box(mat("Sheet_Paper", "#EDEBE4", 0.9), 2.35, 2.56, 0.20, 0.49, TH + 0.12, TH + 0.122)  # check-out sheet
    pk.emit("Bank_PackingTable_Props", bank, tloc, trot)

    # C0: corner unit closing the gap between run B (south wall) and run C, same levels as C
    part, slots_c0, Lc0 = lib["shelf_unit"]([1.17], 0.60, H, lv_c)
    loc_c0, rot_c0 = lib["placement"](21.05 + 0.30, 34.405 + Lc0 / 2, Lc0, 0.60, "+x")
    part.emit("Bank_C0_CornerShelving", bank, loc_c0, rot_c0)
    fill_unit(slots_c0, lv_c, H, 0.60).emit("Bank_C0_Boxes", bank, loc_c0, rot_c0)

    # ---------------- lounge: conversation pit (two facing sofas, poufs, coffee table) by the SSW glass
    conversation_pit(lounge)
    return hidden


hidden = build()
print("bank + lounge built; placeholders hidden:", hidden)
