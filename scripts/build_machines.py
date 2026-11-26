"""Machines from refs/equipment (the list supplied to the architects), as simplified
but recognisable models at the listed sizes. Re-runnable: rebuilds the "Machines"
collection. Run inside Blender: exec(open(path).read()).

Furniture comes from scripts/profile_furniture.py (black 20x20/40x40 profile + birch ply).
Placement (model frame: +X = SSW, +Y = ESE). Laser models are defined here; the laser ROOM is build_laser_room.py.
  Laser room (glazed room x 29.67-32.53, y 20.14-26.92): Epilog Fusion Edge 24 against
  the NNE partition; 2x Glowforge Pro HD, Glowforge Aura, xTool F1 Ultra on profile laser
  tables (sheet storage below) along the SSW glass. ONE central exhaust: the lasers plug into a low
  manifold on the back edge of the tables, one riser, a ceiling collector (Epilog branch joins), one inline
  fan, then up through the slab to the building's dedicated vent higher up.
  Print farm: built by build_print_farm.py (models of all printers live here).
  Mill table in the CNC corner: 2x Roland SRM-20. Craft machines (vinyl cutters, Cricut, Mayku,
  sewing) live in the equipment bank (scripts/build_bank_lounge.py); the SSW glass by the
  entrance is the lounge/entryway.
  CNC: ShopBot PRS Alpha 120 + ACword FT100 dust collector (clearance ignored per the brief).
  Colleague's placeholders in those spots are hidden, not deleted.
"""
import math
import re

import bmesh
import bpy
from mathutils import Matrix, Vector

SOFFIT = 3.93


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def mat(name, hexcol, rough=0.4, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexcol)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = lin(hexcol)
    return m


M = {}


def materials():
    M.update(
        white=mat("Mach_White", "#EEEEEC", 0.35, coat=0.2),
        black=mat("Mach_Black", "#1B1B1C", 0.35),
        grey=mat("Mach_Grey", "#8C9093", 0.4),
        dark=mat("Mach_DarkGrey", "#3A3C3F", 0.4),
        smoke=mat("Mach_SmokedLid", "#2A2420", 0.06, coat=0.6),
        amber=mat("Mach_AmberWindow", "#C25A10", 0.05, coat=0.6),
        purple=mat("Mach_SRMCover", "#5A4A6E", 0.05, coat=0.6),
        red=mat("Mach_EpilogRed", "#C8102E", 0.35),
        orange=mat("Mach_PrusaOrange", "#FA6831", 0.45),
        chrome=mat("Mach_Chrome", "#D8DADC", 0.12, metal=1.0),
        alu=mat("Mach_AluFrame", "#151515", 0.3, metal=0.6),
        pei=mat("Mach_PEI", "#1E1C1A", 0.75),
        lcd=mat("Mach_LCD", "#3D7BD9", 0.2, emit=0.35),
        gold=mat("Mach_Gold", "#C9A24A", 0.3, metal=1.0),
        brass=mat("Mach_Brass", "#B58B4A", 0.3, metal=1.0),
        spoolflange=mat("Spool_Flange", "#202020", 0.35),
        mat_blue=mat("Cricut_Mat", "#6E8FB0", 0.6),
        label=mat("Spool_Label", "#EDEBE4", 0.7),
        srmcover=_make_srm_cover(),
        desk=mat("Desk_Black", "#141414", 0.45),
        rubber=mat("Mach_Rubber", "#0E0E0E", 0.8),
        galv=bpy.data.materials.get("Galvanised") or mat("Galvanised", "#B9BEC2", 0.35, metal=1.0),
        # filament spools in the brand palette
        spools=[mat(f"Filament_{n}", h, 0.3) for n, h in (("Red", "#E03A3F"), ("Green", "#009967"), ("Blue", "#1245DE"),
                                                         ("Orange", "#FFA13D"), ("Yellow", "#F2C200"), ("Pink", "#E099AB"),
                                                         ("White", "#F2F2F0"), ("Black", "#1B1B1C"))],
    )


# ---------------------------------------------------------------- mesh builder
class Part:
    """Collects boxes/cylinders per material in a local frame (x = width, y = depth, front at y=0, z up)."""

    def __init__(self):
        self.bms = {}

    def bm(self, m):
        if m.name not in self.bms:
            self.bms[m.name] = (m, bmesh.new())
        return self.bms[m.name][1]

    def box(self, m, x0, x1, y0, y1, z0, z1, bevel=0.0):
        bm = self.bm(m)
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
        if bevel:
            edges = list({e for v in r["verts"] for e in v.link_edges})
            bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=3, affect="EDGES")

    def cyl(self, m, a, b, r, seg=16):
        a, b = Vector(a), Vector(b)
        d = b - a
        mtx = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.create_cone(self.bm(m), cap_ends=True, segments=seg, radius1=r, radius2=r, depth=d.length, matrix=mtx)

    def emit(self, name, col, loc, rot_z):
        """Place the part: local origin -> loc, rotated about Z by rot_z (radians)."""
        T = Matrix.Translation(loc) @ Matrix.Rotation(rot_z, 4, "Z")
        root = bpy.data.objects.new(name, None)
        col.objects.link(root)
        root.matrix_world = T
        for mname, (m, bm) in self.bms.items():
            me = bpy.data.meshes.new(f"{name}_{mname}")
            bm.to_mesh(me)
            for f in me.polygons:                           # auto-smooth: flat boxes, round cylinders
                f.use_smooth = True
            bm.free()
            me.set_sharp_from_angle(angle=math.radians(30))
            me.materials.append(m)
            o = bpy.data.objects.new(f"{name}_{mname}", me)
            col.objects.link(o)
            o.parent = root
        return root


# ---------------------------------------------------------------- models (front faces -y in local frame)
def desk(w, d=0.6, h=0.75):
    p = Part()
    p.box(M["desk"], 0, w, 0, d, h - 0.025, h, bevel=0.003)
    for x in (0.12, w - 0.12):
        p.box(M["desk"], x - 0.04, x + 0.04, d / 2 - 0.03, d / 2 + 0.03, 0.04, h - 0.025)       # column
        p.box(M["desk"], x - 0.035, x + 0.035, 0.03, d - 0.03, 0.0, 0.04, bevel=0.01)           # foot
    p.box(M["desk"], 0.12, w - 0.12, d / 2 - 0.025, d / 2 + 0.025, h - 0.085, h - 0.025)        # beam
    return p


def _rbox(p, m, x0, x1, y0, y1, z0, z1, r):
    """Rounded box (bevel radius r, clamped)."""
    p.box(m, x0, x1, y0, y1, z0, z1, bevel=min(r, (x1 - x0) / 2.2, (y1 - y0) / 2.2, (z1 - z0) / 2.2))


def _port(p, x, y, z, r, length=0.035):
    """Round exhaust collar sticking out of the back face (y = back) along +y."""
    p.cyl(M["dark"], (x, y - 0.004, z), (x, y + length, z), r + 0.006, seg=28)
    p.cyl(M["black"], (x, y + length - 0.002, z), (x, y + length + 0.001, z), r - 0.004, seg=28)


def glowforge_pro(w=0.965, d=0.527, h=0.211):
    """Glowforge Pro HD (965 x 527 x 211): white rounded shell, smoked lid glass lifting from a rear hinge band,
    front flip-down door with the Pro pass-through slot, glowing button top front right, rear exhaust + switch."""
    p = Part()
    glow = mat("Glowforge_Button", "#9FE7F2", 0.2, emit=3.0)
    # shell: base up to the bed + walls round the cavity under the lid glass (hollow so the bed reads through the
    # tinted lid, branch 2026-11-26), honeycomb crumb tray on the bed
    _rbox(p, M["white"], 0.0, w, 0.0, d, 0.012, 0.035, 0.03)
    for x0, x1, y0, y1 in ((0.0, w, 0.0, 0.05), (0.0, w, d - 0.125, d), (0.0, 0.055, 0.0, d), (w - 0.055, w, 0.0, d)):
        _rbox(p, M["white"], x0, x1, y0, y1, 0.012, h - 0.012, min(0.03, (x1 - x0) / 2 - 0.001, (y1 - y0) / 2 - 0.001))
    liner = mat("Glowforge_Liner", "#26282B", 0.6)                                       # dark cavity, as the real one
    for x0, x1, y0, y1 in ((0.055, w - 0.055, 0.050, 0.054), (0.055, w - 0.055, d - 0.129, d - 0.125),
                           (0.055, 0.059, 0.050, d - 0.125), (w - 0.059, w - 0.055, 0.050, d - 0.125)):
        p.box(liner, x0, x1, y0, y1, 0.035, h - 0.012)
    hc = mat("Honeycomb_Dark", "#4A4D50", 0.5, metal=0.6)
    p.box(hc, 0.07, w - 0.07, 0.06, d - 0.135, 0.035, 0.043)
    for k in range(1, 24):                                                               # tray cells (hint)
        x = 0.07 + k * (w - 0.14) / 24
        p.box(M["dark"], x - 0.0006, x + 0.0006, 0.06, d - 0.135, 0.043, 0.0432)
    for x in (0.06, w - 0.06):                                                           # feet
        for y in (0.06, d - 0.06):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.012), 0.022, seg=16)
    p.box(M["black"], 0.03, w - 0.03, -0.001, 0.0, 0.135, 0.137)                         # door seam (top)
    p.box(M["black"], 0.07, w - 0.07, -0.0015, 0.0, 0.082, 0.090)                        # pass-through slot
    p.box(M["smoke"], 0.10, w - 0.10, -0.002, -0.001, 0.0835, 0.0885)                    # Pro shield in the slot
    for x0, x1, y0, y1 in ((0.03, w - 0.03, 0.030, 0.050), (0.03, w - 0.03, d - 0.125, d - 0.105),
                           (0.03, 0.055, 0.030, d - 0.105), (w - 0.055, w - 0.03, 0.030, d - 0.105)):
        p.box(M["white"], x0, x1, y0, y1, h - 0.012, h - 0.004, bevel=0.002)               # lid frame (ring)
    p.box(_acrylic("Glowforge_LidGlass", "#2A2420", 0.05, alpha=0.30, coat=0.25), 0.055, w - 0.055, 0.050, d - 0.125, h - 0.0045,
          h - 0.0015)                                                                     # lid glass (tinted, see-through)
    _rbox(p, M["white"], 0.02, w - 0.02, d - 0.100, d - 0.012, h - 0.012, h + 0.004, 0.012)  # rear hinge band
    p.box(M["grey"], w * 0.38, w * 0.62, -0.002, 0.018, h - 0.030, h - 0.016, bevel=0.004)   # lid lift recess
    p.cyl(M["white"], (w - 0.075, 0.072, h - 0.006), (w - 0.075, 0.072, h + 0.003), 0.030, seg=32)  # button
    p.cyl(glow, (w - 0.075, 0.072, h + 0.003), (w - 0.075, 0.072, h + 0.004), 0.022, seg=32)
    p.box(M["black"], 0.07, w - 0.07, d, d + 0.0015, 0.082, 0.090)                       # rear pass-through slot
    _port(p, w - 0.12, d, 0.080, 0.05)                                                    # 4" exhaust, rear right
    p.box(M["black"], w - 0.26, w - 0.22, d, d + 0.008, 0.050, 0.070, bevel=0.002)        # power switch
    return p


def glowforge_aura(w=0.556, d=0.521, h=0.127):
    """Glowforge Aura (556 x 521 x 127): low white shell, orange protective lid, button top front right."""
    p = Part()
    glow = mat("Glowforge_Button", "#9FE7F2", 0.2, emit=3.0)
    _rbox(p, M["white"], 0.0, w, 0.0, d, 0.008, h - 0.010, 0.025)
    for x in (0.05, w - 0.05):
        for y in (0.05, d - 0.05):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.008), 0.018, seg=16)
    for x0, x1, y0, y1 in ((0.025, w - 0.025, 0.025, 0.040), (0.025, w - 0.025, d - 0.095, d - 0.080),
                           (0.025, 0.045, 0.025, d - 0.080), (w - 0.045, w - 0.025, 0.025, d - 0.080)):
        p.box(M["white"], x0, x1, y0, y1, h - 0.010, h - 0.004, bevel=0.002)              # lid frame (ring)
    p.box(mat("Aura_Bed", "#232426", 0.6), 0.045, w - 0.045, 0.040, d - 0.095, h - 0.0100, h - 0.0094)   # dark bed
    # lab photo i-002: deep orange see-through window (was an opaque salmon sheet)
    # tinted acrylic filters light (transmission), so the dark bed reads deep orange-brown through it; an alpha
    # blend lit by the windows looked like an opaque salmon sheet
    lid = mat("Aura_OrangeWindow", "#FF7A1C", 0.03)
    _b = next(n_ for n_ in lid.node_tree.nodes if n_.type == "BSDF_PRINCIPLED")
    _b.inputs["Alpha"].default_value = 1.0
    _b.inputs["Transmission Weight"].default_value = 1.0
    _b.inputs["IOR"].default_value = 1.49
    if hasattr(lid, "surface_render_method"):
        lid.surface_render_method = "DITHERED"
    p.box(lid, 0.045, w - 0.045, 0.040, d - 0.095, h - 0.0045, h - 0.0015)                # orange lid
    _rbox(p, M["white"], 0.015, w - 0.015, d - 0.078, d - 0.010, h - 0.010, h + 0.003, 0.010)
    p.box(M["grey"], w * 0.35, w * 0.65, -0.002, 0.014, h - 0.026, h - 0.014, bevel=0.003)
    p.cyl(M["white"], (w - 0.055, 0.055, h - 0.005), (w - 0.055, 0.055, h + 0.002), 0.022, seg=28)
    p.cyl(glow, (w - 0.055, 0.055, h + 0.002), (w - 0.055, 0.055, h + 0.003), 0.016, seg=28)
    _port(p, w - 0.11, d, 0.060, 0.05)
    return p


def _acrylic(name, hexcol, rough=0.08, alpha=0.45, coat=0.8):
    """Tinted acrylic sheet without refraction (alpha-blended colour + clear-coat reflections): thin sheets
    modelled as boxes otherwise render like warped chrome."""
    m = mat(name, hexcol, rough, coat=coat)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Transmission Weight"].default_value = 0.0
    b.inputs["Alpha"].default_value = alpha
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    return m


def xtool_f1_ultra(w=0.273, d=0.373, h=0.492):
    """xTool F1 Ultra (273 W x 373 D x 492 H, upright galvo tower; checked against xTool product photos):
    translucent green acrylic shield on the front + left side that lifts by a low silver handle, a more solid
    green upper band (galvo housing behind, XTOOL wordmark), grey aluminium right-side panel with the orange-red
    E-stop and a button strip, dark top, ribbed slatted back wall inside, silver base plate on feet, rear smoke
    outlet. The touchscreen controller is a separate object (xtool_controller)."""
    p = Part()
    green = _acrylic("xTool_Green", "#36A826", 0.06, 0.26)
    band = _acrylic("xTool_Green_Band", "#45B82F", 0.20, 0.88)
    alu = mat("xTool_Alu", "#8E9296", 0.35, metal=0.7)
    t, sp = 0.004, 0.022                                                   # acrylic thickness, right panel
    p.box(alu, 0.0, w, 0.0, d, 0.010, 0.020, bevel=0.002)                  # base plate
    for x in (0.03, w - 0.03):
        for y in (0.03, d - 0.03):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.010), 0.012, seg=12)
    p.box(alu, w - sp, w, 0.0, d, 0.020, h, bevel=0.003)                   # right side panel (body spine)
    p.box(M["dark"], 0.0, w, 0.0, d, h - 0.012, h, bevel=0.003)            # top
    p.box(M["dark"], 0.004, w - sp, d - 0.012, d, 0.020, h - 0.012)        # back panel
    zb = 0.315                                                             # bottom of the solid upper band
    p.box(green, 0.0, w - sp, 0.0, t, 0.020, zb)                           # front shield (clear part)
    p.box(green, 0.0, t, t, d - 0.012, 0.020, zb)                          # left shield (clear part)
    p.box(band, 0.0, w - sp, 0.0, t, zb, h - 0.012)                        # upper band, front
    p.box(band, 0.0, t, t, d - 0.012, zb, h - 0.012)                       # upper band, left
    p.box(M["dark"], t, w - sp, t, d - 0.012, zb, h - 0.014)               # galvo housing behind the band
    p.cyl(M["black"], (w * 0.45, d * 0.45, zb - 0.010), (w * 0.45, d * 0.45, zb), 0.030, seg=24)   # lens
    for k in range(12):                                                    # ribbed back wall inside
        x = 0.012 + k * (w - sp - 0.024) / 11
        p.box(M["black"], x, x + 0.010, d - 0.030, d - 0.012, 0.020, zb)
    p.box(M["black"], t, w - sp, t, d - 0.030, 0.020, 0.024)               # slatted work panel
    p.box(alu, 0.05, 0.17, -0.016, -0.004, 0.034, 0.042, bevel=0.003)      # front lift handle
    for x in (0.055, 0.165):
        p.box(alu, x - 0.004, x + 0.004, -0.006, t, 0.034, 0.042)
    estop = mat("xTool_EStop", "#E2462B", 0.35)
    p.cyl(M["dark"], (w, d * 0.30, 0.17), (w + 0.010, d * 0.30, 0.17), 0.020, seg=20)
    p.cyl(estop, (w + 0.010, d * 0.30, 0.17), (w + 0.026, d * 0.30, 0.17), 0.016, seg=20)
    p.box(M["black"], w, w + 0.004, d * 0.20, d * 0.24, 0.06, 0.15, bevel=0.002)   # button strip
    _port(p, (w - sp) / 2, d, 0.22, 0.045)                                 # rear smoke outlet
    return p


def xtool_controller():
    """F1 Ultra touchscreen controller (separate, ~130 x 90 x 30 mm): black body, green base strip, screen, loop."""
    p = Part()
    p.box(M["black"], 0.0, 0.13, 0.0, 0.032, 0.006, 0.090, bevel=0.006)
    p.box(mat("xTool_Green_Strip", "#3FD12C", 0.4), 0.0, 0.13, 0.0, 0.032, 0.0, 0.008, bevel=0.002)
    p.box(mat("xTool_Screen", "#1C2A22", 0.15, emit=0.4), 0.012, 0.100, -0.001, 0.0, 0.020, 0.078)
    p.box(mat("xTool_Green_Strip", "#3FD12C", 0.4), 0.035, 0.075, -0.0015, -0.001, 0.045, 0.053)
    for k in range(3):
        p.box(M["dark"], 0.108, 0.122, -0.001, 0.0, 0.025 + k * 0.022, 0.039 + k * 0.022)
    p.cyl(M["black"], (0.035, 0.016, 0.090), (0.035, 0.016, 0.120), 0.003, seg=8)
    p.cyl(M["black"], (0.095, 0.016, 0.090), (0.095, 0.016, 0.120), 0.003, seg=8)
    p.cyl(M["black"], (0.035, 0.016, 0.120), (0.095, 0.016, 0.120), 0.003, seg=8)
    return p


def epilog(w=1.055, d=0.834, h=0.967):
    """Epilog Fusion Edge 24 (1055 x 834 x 967 incl. stand; checked against Epilog product photos): WHITE machine on
    a white open-front stand with a shelf, casters with orange rings; light-grey full-height corner pillars; pale
    grey front door panel, yellow warning label; navy band across the lid front (logo + "Fusion Edge" text are
    separate font objects); lid with a big dark viewing window; small raised housings top-left and top-right
    (control screen); rear 4" exhaust."""
    p = Part()
    navy = mat("Epilog_Navy", "#21457E", 0.35, coat=0.3)
    pil = mat("Epilog_Pillar", "#D5D8DB", 0.35, coat=0.2)
    door = mat("Epilog_Door", "#E4E6E8", 0.4)
    ring = mat("Epilog_CasterRing", "#E07B24", 0.4)
    sticker = mat("Safety_Yellow", "#F2C200", 0.4)
    wh = M["white"]
    pw, zs, zb, zl = 0.085, 0.40, 0.80, 0.93                              # pillar width, stand top, band, lid
    for x in (0.08, w - 0.08):                                            # casters
        for y in (0.08, d - 0.08):
            p.cyl(M["rubber"], (x - 0.016, y, 0.035), (x + 0.016, y, 0.035), 0.035, seg=20)
            p.cyl(ring, (x, y, 0.062), (x, y, 0.075), 0.030, seg=20)
    # stand: open front box with a shelf
    p.box(wh, pw, w - pw, d - 0.03, d, 0.075, zs)                         # back
    p.box(wh, pw, w - pw, 0.02, d - 0.03, 0.075, 0.095)                   # bottom
    p.box(wh, pw, w - pw, 0.05, d - 0.03, 0.20, 0.215)                    # shelf
    p.box(M["dark"], pw, w - pw, 0.10, d - 0.031, 0.095, 0.20)            # shadowed interior back
    # corner pillars, full height
    for x0 in (0.0, w - pw):
        _rbox(p, pil, x0, x0 + pw, 0.0, d, 0.075, zl, 0.008)
    # body between the pillars
    p.box(wh, pw, w - pw, 0.012, d, zs, zb)                               # body shell
    p.box(door, pw + 0.01, w - pw - 0.01, 0.0, 0.014, zs + 0.02, zb - 0.09)   # front door panel
    p.box(M["grey"], pw + 0.01, w - pw - 0.01, -0.001, 0.0, zb - 0.092, zb - 0.088)  # door seam
    p.box(sticker, w * 0.60, w * 0.65, -0.002, 0.0, zb - 0.07, zb - 0.035)    # warning label
    p.box(M["black"], w * 0.66, w * 0.71, -0.002, 0.0, zb - 0.07, zb - 0.035)
    # lid: navy front band + white top with the dark window
    p.box(navy, pw, w - pw, 0.0, 0.03, zb, zl, bevel=0.004)
    p.box(wh, pw, w - pw, 0.03, d, zb, zl - 0.004)
    _rbox(p, wh, 0.0, w, 0.0, d * 0.82, zl, h - 0.012, 0.010)
    p.box(M["smoke"], 0.13, w - 0.13, 0.05, d * 0.72, h - 0.012, h - 0.009)    # viewing window
    p.box(navy, 0.11, w - 0.11, 0.035, 0.05, h - 0.013, h - 0.010)            # window frame lip (front)
    p.box(wh, 0.0, w, d * 0.82, d, zl, h - 0.020, bevel=0.008)               # rear hinge housing
    _rbox(p, wh, 0.03, 0.17, 0.05, 0.22, h - 0.012, h + 0.020, 0.008)        # top-left housing
    _rbox(p, wh, w - 0.20, w - 0.03, 0.04, 0.24, h - 0.012, h + 0.024, 0.008)  # control housing
    p.box(M["black"], w - 0.18, w - 0.05, 0.06, 0.15, h + 0.024, h + 0.026)    # control screen
    p.box(M["lcd"], w - 0.17, w - 0.06, 0.07, 0.14, h + 0.026, h + 0.027)
    _port(p, w / 2 + 0.25, d, 0.70, 0.05)                                     # rear 4" exhaust
    return p


PRINT_RNG = __import__('random').Random(5)


def _make_srm_cover():
    """Smoked violet polycarbonate: mostly transmissive glass."""
    m = bpy.data.materials.get("SRM_Cover") or bpy.data.materials.new("SRM_Cover")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    g = nt.nodes.new("ShaderNodeBsdfPrincipled")
    g.inputs["Base Color"].default_value = lin("#7A6A9A")
    g.inputs["Roughness"].default_value = 0.05
    g.inputs["Transmission Weight"].default_value = 0.85
    g.inputs["IOR"].default_value = 1.58
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(g.outputs[0], o.inputs["Surface"])
    m.diffuse_color = (*lin("#7A6A9A")[:3], 0.4)
    return m


def spool_part(p, filament, cx, cy, cz, axis="x", r_out=0.100, width=0.065):
    """Real filament spool: two thin flanges, cardboard/plastic hub, wound filament, axis along x."""
    ax = Vector((1, 0, 0)) if axis == "x" else Vector((0, 1, 0))
    c = Vector((cx, cy, cz))
    for side in (-1, 1):
        a0 = c + ax * side * (width / 2)
        p.cyl(M["spoolflange"], a0 - ax * 0.002, a0 + ax * 0.002, r_out, seg=48)
    p.cyl(filament, c - ax * (width / 2 - 0.003), c + ax * (width / 2 - 0.003), r_out * 0.82, seg=48)
    for k in range(1, 9):                                                    # wound-filament grooves
        g = c - ax * (width / 2 - 0.003) + ax * (width - 0.006) * k / 9
        p.cyl(M["dark"], g - ax * 0.0004, g + ax * 0.0004, r_out * 0.821, seg=48)
    lab = c + ax * (width / 2 + 0.0025)                                          # label on the outer flange
    p.cyl(M["label"], lab, lab + ax * 0.0006, 0.045, seg=32)
    p.cyl(M["dark"], c - ax * (width / 2 + 0.003), c + ax * (width / 2 + 0.003), 0.027, seg=24)


def prusa(spool, zx=0.20, random_print=True):
    """Prusa MK3S+ (~500 x 550 x 400): frame plate, rods, motors, PEI bed, orange parts, LCD, spool on top. zx = X-axis
    height (nozzle tip at zx - 0.05 above the base; the PEI top is at 0.064), so a print job can sit under the nozzle."""
    p = Part()
    w, d = 0.50, 0.55
    fy = 0.31                                                                                    # frame plane (y)
    # --- base: Y frame (aluminium extrusions + printed corners) and the PSU at the back
    for x in (0.10, w - 0.12):
        p.box(M["alu"], x, x + 0.02, 0.03, d - 0.03, 0.0, 0.03, bevel=0.002)
    for y in (0.03, d - 0.06):
        p.box(M["orange"], 0.07, w - 0.07, y, y + 0.03, 0.0, 0.05, bevel=0.004)
    p.box(M["black"], w - 0.11, w - 0.02, fy + 0.02, d - 0.05, 0.0, 0.07, bevel=0.003)          # PSU
    # --- Y axis: smooth rods + carriage + heatbed
    for x in (0.16, w - 0.16):
        p.cyl(M["chrome"], (x, 0.06, 0.035), (x, d - 0.06, 0.035), 0.004, seg=10)
    bed_y = 0.12
    p.box(M["alu"], 0.12, w - 0.12, bed_y, bed_y + 0.25, 0.048, 0.054)                          # Y carriage
    p.box(mat("Prusa_SatinSheet", "#4F5648", 0.72), 0.125, w - 0.125, bed_y - 0.005, bed_y + 0.255, 0.060, 0.064,
          bevel=0.002)                                                                # satin sheet (lab photo i-006)
    p.box(M["gold"], 0.124, w - 0.124, bed_y - 0.006, bed_y + 0.256, 0.058, 0.0605)             # sheet edge
    # --- main frame plate (black aluminium) with its big window: four bars
    t = 0.006
    p.box(M["alu"], 0.02, 0.08, fy, fy + t, 0.0, 0.40, bevel=0.002)                              # left post
    p.box(M["alu"], w - 0.08, w - 0.02, fy, fy + t, 0.0, 0.40, bevel=0.002)                      # right post
    p.box(M["alu"], 0.02, w - 0.02, fy, fy + t, 0.35, 0.40, bevel=0.002)                         # top bar
    p.box(M["alu"], 0.02, w - 0.02, fy, fy + t, 0.0, 0.07, bevel=0.002)                          # bottom bar
    # --- Z axis: motors at the bottom, threaded + smooth rods, top bracket
    for x in (0.05, w - 0.05):
        p.box(M["black"], x - 0.021, x + 0.021, fy - 0.045, fy - 0.003, 0.0, 0.042, bevel=0.003)  # NEMA17
        p.box(M["chrome"], x - 0.021, x + 0.021, fy - 0.045, fy - 0.003, 0.042, 0.046)
        p.cyl(M["brass"], (x, fy - 0.024, 0.046), (x, fy - 0.024, 0.37), 0.004, seg=10)          # leadscrew
        p.cyl(M["chrome"], (x + 0.03 * (1 if x < w / 2 else -1), fy - 0.024, 0.07),
              (x + 0.03 * (1 if x < w / 2 else -1), fy - 0.024, 0.38), 0.004, seg=10)
        p.box(M["orange"], x - 0.03, x + 0.04 if x < w / 2 else x + 0.03, fy - 0.05, fy, 0.37, 0.40, bevel=0.004)
    # --- X axis at print height: two rods, X-ends, extruder + fan + nozzle
    for dz in (0.0, 0.045):
        p.cyl(M["chrome"], (0.07, fy - 0.035, zx + dz), (w - 0.07, fy - 0.035, zx + dz), 0.004, seg=10)
    for x0 in (0.035, w - 0.095):
        p.box(M["orange"], x0, x0 + 0.06, fy - 0.06, fy - 0.004, zx - 0.025, zx + 0.07, bevel=0.005)
    p.box(M["black"], 0.025, 0.07, fy - 0.10, fy - 0.06, zx - 0.02, zx + 0.025, bevel=0.003)      # X motor
    ex = w * 0.42
    p.box(M["orange"], ex, ex + 0.07, fy - 0.10, fy - 0.03, zx - 0.03, zx + 0.10, bevel=0.006)    # extruder body
    p.box(M["black"], ex + 0.012, ex + 0.058, fy - 0.112, fy - 0.10, zx + 0.0, zx + 0.05, bevel=0.003)  # hotend fan
    p.box(M["black"], ex + 0.015, ex + 0.055, fy - 0.07, fy - 0.03, zx + 0.10, zx + 0.14, bevel=0.003)  # extruder motor
    p.cyl(M["brass"], (ex + 0.035, fy - 0.07, zx - 0.03), (ex + 0.035, fy - 0.07, zx - 0.05), 0.004, seg=10)  # nozzle
    p.cyl(M["dark"], (ex + 0.035, fy - 0.07, zx + 0.14), (ex + 0.035, fy + 0.04, 0.47), 0.003, seg=8)   # PTFE/filament path
    # --- close-up detail: screw heads on printed parts, hotend fan grille, sleeved cable bundle
    def screws(x0, x1, z0, z1, yface, n=2):
        for i in range(n):
            for zz in (z0 + 0.012, z1 - 0.012):
                xx = x0 + (i + 0.5) * (x1 - x0) / n
                p.cyl(M["chrome"], (xx, yface - 0.0015, zz), (xx, yface, zz), 0.0028, seg=10)
    screws(ex, ex + 0.07, zx - 0.03, zx + 0.10, fy - 0.10)
    for x0 in (0.035, w - 0.095):
        screws(x0, x0 + 0.06, zx - 0.025, zx + 0.07, fy - 0.06, n=1)
    for k in range(4):                                                                          # fan grille rings
        r = 0.006 + k * 0.0045
        p.cyl(M["dark"], (ex + 0.035, fy - 0.1125, zx + 0.025), (ex + 0.035, fy - 0.1121, zx + 0.025), r, seg=24)
        p.cyl(M["black"], (ex + 0.035, fy - 0.1127, zx + 0.025), (ex + 0.035, fy - 0.1123, zx + 0.025), r - 0.0018, seg=24)
    for k in range(5):                                                                          # sleeved bundle arc to the frame
        t0, t1 = k / 5, (k + 1) / 5
        a = (ex + 0.05 + t0 * 0.12, fy - 0.03 + t0 * 0.03, zx + 0.10 + 0.08 * (1 - (2 * t0 - 1) ** 2))
        b = (ex + 0.05 + t1 * 0.12, fy - 0.03 + t1 * 0.03, zx + 0.10 + 0.08 * (1 - (2 * t1 - 1) ** 2))
        p.cyl(M["black"], a, b, 0.006, seg=10)
    # --- LCD unit at the front left (branch remodel): printed housing with the face tilted back 25 deg, 20 x 4
    # character display (white on blue) in a black bezel, knurled knob, reset button, SD slot, beeper grille
    tilt = math.radians(25)
    face = Matrix.Translation((0.23, -0.012, 0.048)) @ Matrix.Rotation(-tilt, 4, "X")       # face frame: x right, z up
    def fbox(m, x0, x1, z0, z1, n0, n1):
        bmesh.ops.create_cube(p.bm(m), size=1.0, matrix=face @ Matrix.Translation(((x0 + x1) / 2, -(n0 + n1) / 2,
                              (z0 + z1) / 2)) @ Matrix.Diagonal((x1 - x0, abs(n1 - n0), z1 - z0, 1)))
    p.box(M["orange"], 0.10, 0.36, -0.01, 0.03, 0.008, 0.07, bevel=0.005)                    # housing body
    fbox(M["orange"], -0.13, 0.13, -0.042, 0.042, 0.0, 0.03)                                  # tilted front block
    fbox(M["black"], -0.115, 0.04, -0.03, 0.03, 0.03, 0.032)                                  # bezel
    fbox(M["lcd"], -0.105, 0.03, -0.022, 0.022, 0.032, 0.0325)                                # display
    txt = mat("LCD_Text", "#F4F8FF", 0.4, emit=1.5)
    for r, n in enumerate((14, 18, 11, 16)):                                                  # character rows
        for c in range(n):
            x = -0.10 + c * 0.0062
            z = 0.014 - r * 0.0105
            fbox(txt, x, x + 0.0045, z - 0.0035, z + 0.0035, 0.0325, 0.0328)
    for k in range(16):                                                                       # knurled knob
        a_ = 2 * math.pi * k / 16
        fbox(M["dark"], 0.075 + 0.0105 * math.cos(a_) - 0.0016, 0.075 + 0.0105 * math.cos(a_) + 0.0016,
             0.006 + 0.0105 * math.sin(a_) - 0.0016, 0.006 + 0.0105 * math.sin(a_) + 0.0016, 0.03, 0.045)
    fbox(M["dark"], 0.075 - 0.0095, 0.075 + 0.0095, 0.006 - 0.0095, 0.006 + 0.0095, 0.03, 0.046)
    fbox(M["black"], 0.104, 0.112, -0.03, -0.022, 0.03, 0.034)                                # reset button
    for k in range(4):
        fbox(M["black"], 0.064 + k * 0.006, 0.067 + k * 0.006, -0.032, -0.024, 0.03, 0.0305)  # beeper grille
    p.box(M["black"], 0.098, 0.1005, 0.0, 0.02, 0.02, 0.026)                                  # SD slot (left side)
    # --- spool holder on the top bar + spool
    p.box(M["orange"], w / 2 - 0.012, w / 2 + 0.012, fy - 0.01, fy + 0.03, 0.40, 0.46, bevel=0.003)
    spool_part(p, spool, w / 2, fy + 0.045, 0.47)
    _pp = Part() if not random_print else p                                                    # keep RNG draws stable
    if PRINT_RNG.random() < 0.55:                                              # a print in progress
        kind = PRINT_RNG.choice(("box", "vase", "bracket"))
        bx, by = w / 2 + PRINT_RNG.uniform(-0.06, 0.06), bed_y + 0.12 + PRINT_RNG.uniform(-0.04, 0.04)
        hgt = PRINT_RNG.uniform(0.015, 0.09)
        if kind == "vase":
            _pp.cyl(spool, (bx, by, 0.064), (bx, by, 0.064 + hgt), PRINT_RNG.uniform(0.025, 0.045), seg=40)
        elif kind == "box":
            sx, sy = PRINT_RNG.uniform(0.03, 0.09), PRINT_RNG.uniform(0.03, 0.09)
            _pp.box(spool, bx - sx / 2, bx + sx / 2, by - sy / 2, by + sy / 2, 0.064, 0.064 + hgt, bevel=0.002)
        else:
            _pp.box(spool, bx - 0.05, bx + 0.05, by - 0.015, by + 0.015, 0.064, 0.072, bevel=0.0015)
            _pp.box(spool, bx - 0.05, bx - 0.04, by - 0.015, by + 0.015, 0.072, 0.064 + hgt, bevel=0.0015)
    return p


def bambu(w=0.392, d=0.406, h=0.478, ams=False):
    p = Part()
    p.box(M["dark"], 0, w, 0, d, 0, h, bevel=0.01)
    p.box(M["smoke"], 0.02, w - 0.02, -0.004, 0.01, 0.06, h - 0.03, bevel=0.004)               # glass door
    p.box(M["smoke"], 0.02, w - 0.02, 0.02, d - 0.02, h, h + 0.004)                             # glass top
    if ams:
        ams_2_pro(p, (w - 0.372) / 2, (d - 0.280) / 2, h + 0.004)
    return p


def ams_2_pro(p, x0, y0, z0, spools=None):
    """Bambu Lab AMS 2 Pro, 372 x 280 x 226 mm (spec sheet), from the bambulab.com product photos: dark grey
    tub with a smoked translucent front, four feeder units behind it, and a smoked half-round lid over four spools
    lying side by side (axes along the width). Front at y0."""
    W, D, Hb, R = 0.372, 0.280, 0.115, 0.111                       # Hb + R = 0.226
    tint = _acrylic("AMS_Smoke", "#3A3430", 0.05, 0.55)
    grey = mat("AMS_Grey", "#2B2D30", 0.45)
    p.box(grey, x0, x0 + W, y0, y0 + D, z0, z0 + 0.012, bevel=0.004)              # foot plate
    p.box(grey, x0, x0 + 0.018, y0, y0 + D, z0, z0 + Hb, bevel=0.005)             # side cheeks
    p.box(grey, x0 + W - 0.018, x0 + W, y0, y0 + D, z0, z0 + Hb, bevel=0.005)
    p.box(grey, x0 + 0.018, x0 + W - 0.018, y0 + 0.04, y0 + D, z0, z0 + Hb - 0.004)   # tub behind the front
    p.box(tint, x0 + 0.018, x0 + W - 0.018, y0 + 0.002, y0 + 0.008, z0 + 0.012, z0 + Hb)   # smoked front
    p.box(grey, x0 + 0.018, x0 + W - 0.018, y0, y0 + D, z0 + Hb - 0.006, z0 + Hb, bevel=0.002)  # rim
    for k in range(4):                                                            # feeders, seen through the front
        fx = x0 + 0.045 + k * 0.094
        p.cyl(M["dark"], Vector((fx, y0 + 0.03, z0 + 0.012)), Vector((fx, y0 + 0.03, z0 + 0.07)), 0.022, seg=20)
        p.box(mat("AMS_Gear", "#B36A2C", 0.5), fx - 0.008, fx + 0.008, y0 + 0.022, y0 + 0.04, z0 + 0.07, z0 + 0.09)
    cy, cz = y0 + D / 2, z0 + Hb                                                  # half-round lid (lower half hidden)
    p.cyl(tint, Vector((x0 + 0.02, cy, cz)), Vector((x0 + W - 0.02, cy, cz)), R, seg=48)
    for k, fil in enumerate(spools or [M["spools"][i % len(M["spools"])] for i in (1, 4, 2, 6)]):
        spool_part(p, fil, x0 + 0.054 + k * 0.088, cy, cz - 0.005, axis="x", r_out=0.100, width=0.064)
    p.box(M["white"], x0 + W - 0.07, x0 + W - 0.03, y0 + 0.004, y0 + 0.012, z0 + Hb - 0.03, z0 + Hb - 0.018)  # label


def srm20(w=0.451, d=0.426, h=0.426, tip=0.13):
    """Roland SRM-20: white shell (base, sides, back, roof) + smoked violet see-through front cover;
    inside: aluminium bed with a copper blank, spindle on its Z carriage."""
    p = Part()
    p.box(M["white"], 0, w, 0.0, d, 0, 0.10, bevel=0.012)                                   # base
    p.box(M["white"], 0, 0.045, 0.0, d, 0.10, h, bevel=0.01)                                # left side
    p.box(M["white"], w - 0.045, w, 0.0, d, 0.10, h, bevel=0.01)                            # right side
    p.box(M["white"], 0.045, w - 0.045, d - 0.06, d, 0.10, h, bevel=0.008)                  # back
    p.box(M["white"], 0.0, w, 0.10, d, h - 0.03, h, bevel=0.01)                             # roof
    p.box(M["srmcover"], 0.045, w - 0.045, 0.0, 0.006, 0.10, h - 0.03)                      # front cover (see-through)
    p.box(M["srmcover"], 0.045, w - 0.045, 0.006, 0.10, h - 0.036, h - 0.03)                # cover top lip
    p.box(M["alusatin"] if "alusatin" in M else M["chrome"], 0.08, w - 0.08, 0.10, d - 0.10, 0.10, 0.115)   # bed
    p.box(M["gold"], 0.13, 0.27, 0.15, 0.27, 0.115, 0.117)                                  # copper blank
    p.box(M["white"], w * 0.40, w * 0.62, d - 0.16, d - 0.06, 0.20, h - 0.03, bevel=0.006)  # Z carriage
    dz = tip - 0.13                                                                            # tip = end-mill tip height
    p.cyl(M["dark"], (w * 0.51, d - 0.17, 0.17 + dz), (w * 0.51, d - 0.17, 0.30 + dz), 0.022, seg=24)  # spindle motor
    p.cyl(M["chrome"], (w * 0.51, d - 0.17, tip), (w * 0.51, d - 0.17, 0.17 + dz), 0.004, seg=8)      # end mill
    p.box(M["lcd"], w - 0.04, w - 0.02, -0.001, 0.0, 0.05, 0.07)                            # status LED
    return p


def vinyl(w=0.851, d=0.310, h=0.235):
    """Roland CAMM-1 GS-24 desktop vinyl cutter (both of the lab's are GS-24s): grey body, black end caps, pinch-roller slot, vinyl roll behind."""
    p = Part()
    char = mat("GS24_Charcoal", "#2B2C2F", 0.45)                                              # lab photo i-010
    p.box(char, 0.07, w - 0.07, 0.05, d - 0.02, 0.03, h, bevel=0.025)
    p.box(mat("GS24_FrontSilver", "#A9ADB1", 0.35, metal=0.5), 0.07, w - 0.07, 0.048, 0.052, 0.04, 0.098)  # lower front
    for x0 in (0.0, w - 0.07):
        p.box(M["black"], x0, x0 + 0.07, 0.02, d, 0.0, h + 0.01, bevel=0.02)
    p.box(M["black"], 0.07, w - 0.07, 0.035, 0.07, 0.10, 0.125, bevel=0.003)                  # media slot
    for k, x in enumerate((0.095, 0.112, 0.130, 0.149, 0.166, 0.184)):                        # Roland wordmark hint
        p.box(M["white"], x, x + 0.012, 0.0485, 0.049, h - 0.045, h - 0.030)
    p.box(M["white"], 0.10, w - 0.10, 0.02, 0.05, 0.106, 0.110)                               # vinyl coming out
    p.box(M["black"], w - 0.16, w - 0.08, 0.16, 0.26, h - 0.002, h + 0.006, bevel=0.003)      # control panel
    p.box(M["lcd"], w - 0.15, w - 0.11, 0.18, 0.21, h + 0.006, h + 0.007)
    p.cyl(M["spools"][2], (0.12, d + 0.07, 0.07), (w - 0.12, d + 0.07, 0.07), 0.04, seg=32)   # roll on stand
    p.cyl(M["chrome"], (0.08, d + 0.07, 0.07), (w - 0.08, d + 0.07, 0.07), 0.008, seg=12)
    return p


def mayku(w=0.274, d=0.466, h=0.315):
    """Mayku FormBox (the list's 274 x 466 x 315 footprint; look from the lab photo i-011): light grey base with a
    dark top frame and the vacuum bed, two yellow knobs on the front, the forming frame (light grey, yellow handles on
    both long sides) clamped down, two chrome posts at the back, dark grey heater hood up top with a yellow handle."""
    p = Part()
    base = mat("Mayku_Base", "#D5D7D6", 0.45)
    grey = mat("Mayku_Grey", "#5E6267", 0.4)
    yel = mat("Mayku_Yellow", "#F2B705", 0.4)
    _rbox(p, base, 0.0, w, 0.0, d, 0.0, 0.085, 0.02)                                      # base
    p.box(grey, 0.015, w - 0.015, 0.015, d - 0.07, 0.085, 0.092, bevel=0.002)             # top frame
    p.box(mat("Mayku_Bed", "#2E3033", 0.7), 0.035, w - 0.035, 0.035, d - 0.09, 0.0921, 0.0925)  # perforated bed
    for x in (0.08, w - 0.08):
        p.cyl(yel, (x, -0.012, 0.045), (x, 0.0, 0.045), 0.016, seg=24)                    # front knobs
    p.box(base, 0.01, w - 0.01, 0.01, d - 0.065, 0.093, 0.108, bevel=0.003)               # forming frame (clamped)
    p.box(M["smoke"], 0.04, w - 0.04, 0.04, d - 0.095, 0.1075, 0.1085)                     # sheet in the frame
    for x0 in (-0.022, w):
        p.box(yel, x0, x0 + 0.022, d * 0.30, d * 0.62, 0.095, 0.106, bevel=0.003)          # frame handles
    for x in (0.03, w - 0.03):
        p.cyl(M["chrome"], (x, d - 0.035, 0.085), (x, d - 0.035, h - 0.05), 0.009, seg=16)  # posts
    _rbox(p, grey, -0.005, w + 0.005, 0.0, d, h - 0.075, h, 0.018)                         # heater hood
    p.box(mat("Mayku_Heater", "#1A1B1D", 0.6), 0.02, w - 0.02, 0.02, d - 0.07, h - 0.076, h - 0.075)  # element face
    p.box(yel, w + 0.004, w + 0.024, d * 0.35, d * 0.58, h - 0.055, h - 0.035, bevel=0.003)  # hood handle
    return p

def _rounded_poly(pts, radii, seg=6):
    """Closed 2D polygon with each corner replaced by a quadratic fillet of radius r (0 = sharp)."""
    out = []
    n = len(pts)
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        r = radii[i]
        if r <= 0:
            out.append(p1)
            continue
        a = p1 + (p0 - p1).normalized() * min(r, (p0 - p1).length / 2)
        b = p1 + (p2 - p1).normalized() * min(r, (p2 - p1).length / 2)
        for k in range(seg + 1):
            t = k / seg
            out.append(a * (1 - t) ** 2 + p1 * 2 * (1 - t) * t + b * t * t)
    return [(v.x, v.y) for v in out]


def _prism_xz(p, m, pts, y0, y1, bevel=0.0):
    """Prism from a 2D outline (x, z) in the front plane, extruded from y0 to y1, edges optionally bevelled."""
    import bmesh
    bm = p.bm(m)
    vs = [bm.verts.new((x, y0, z)) for x, z in pts]
    f = bm.faces.new(vs)
    ex = bmesh.ops.extrude_face_region(bm, geom=[f])
    nv = [g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=nv, vec=(0, y1 - y0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if bevel:
        ring = [e for e in bm.edges if e.verts[0] in set(vs + nv) and e.verts[1] in set(vs + nv)
                and abs(e.verts[0].co.y - e.verts[1].co.y) < 1e-6]
        bmesh.ops.bevel(bm, geom=ring, offset=bevel, segments=3, affect="EDGES", clamp_overlap=True)


def _cone(p, m, a, b, r0, r1, seg=20):
    import bmesh
    a, b = Vector(a), Vector(b)
    d = b - a
    mtx = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cone(p.bm(m), cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=d.length, matrix=mtx)


def _sew_body(p, x0, w, d, h, screen_w=0.08):
    """Computerised sewing-machine body (Brother Innov-is style) in the local frame, front at y=0, starting at x0.
    Returns the needle (x, y)."""
    wh, gry, dk = M["white"], mat("Sew_Grey", "#B8BEC6", 0.4), M["dark"]
    X = lambda v: x0 + v
    _prism_xz(p, wh, _rounded_poly([(X(0), 0), (X(w), 0), (X(w), 0.075), (X(0), 0.075)], [0.01, 0.01, 0.02, 0.02]),
              0.0, d, bevel=0.006)                                                         # bed
    yf, yb = 0.035, d - 0.035
    c = [(X(0.025), 0.115), (X(0.115), 0.115), (X(0.115), 0.205), (X(w - 0.125), 0.205), (X(w - 0.125), 0.07),
         (X(w - 0.012), 0.07), (X(w - 0.012), h), (X(0.025), h - 0.004)]
    _prism_xz(p, wh, _rounded_poly(c, [0.012, 0.008, 0.03, 0.03, 0, 0, 0.05, 0.035]), yf, yb, bevel=0.008)   # arm
    p.box(gry, X(0.13), X(w - 0.14), yf - 0.002, yf, 0.215, h - 0.02, bevel=0.002)        # grey arm-front panel
    p.box(dk, X(0.135), X(w - 0.15), yf - 0.0025, yf - 0.002, 0.25, 0.252)                # thread-path groove
    p.box(dk, X(0.088), X(0.096), yf - 0.002, yf, 0.18, 0.272)                             # take-up lever slot
    p.box(gry, X(0.084), X(0.100), yf - 0.012, yf - 0.002, 0.236, 0.246, bevel=0.002)     # take-up lever
    for i, cc in enumerate(("#2E7D32", "#C62828", "#455A64", "#455A64")):                 # start/stop, reverse, needle, cut
        bm_ = mat(f"Sew_Btn_{cc[1:]}", cc, 0.4)
        p.box(bm_, X(0.032 + i * 0.02), X(0.047 + i * 0.02), yf - 0.004, yf, 0.255, 0.268, bevel=0.002)
    p.box(dk, X(0.035), X(0.11), yf - 0.0025, yf - 0.002, 0.24, 0.244)                   # speed slider slot
    p.box(gry, X(0.06), X(0.07), yf - 0.006, yf - 0.002, 0.236, 0.248, bevel=0.0015)
    sx0 = w - 0.012 - 0.01 - screen_w                                                      # screen + keys on the pillar
    p.box(dk, X(sx0), X(sx0 + screen_w), yf - 0.003, yf, 0.15, 0.20, bevel=0.002)
    p.box(M["lcd"], X(sx0 + 0.004), X(sx0 + screen_w - 0.004), yf - 0.0035, yf - 0.003, 0.155, 0.195)
    for k in range(3):
        for r in range(2):
            p.box(gry, X(sx0 + 0.006 + k * screen_w / 3), X(sx0 + 0.018 + k * screen_w / 3), yf - 0.003, yf,
                  0.10 + r * 0.02, 0.112 + r * 0.02, bevel=0.0015)
    hy, hz = d / 2, 0.21                                                                   # hand wheel (right side)
    p.cyl(wh, (X(w - 0.012), hy, hz), (X(w + 0.004), hy, hz), 0.046, seg=36)
    p.cyl(gry, (X(w + 0.004), hy, hz), (X(w + 0.016), hy, hz), 0.044, seg=36)
    p.cyl(dk, (X(w + 0.016), hy, hz), (X(w + 0.018), hy, hz), 0.012, seg=20)
    nx, ny = 0.07, 0.085                                                                   # needle position
    ch = M["chrome"]
    p.cyl(ch, (X(nx), ny, 0.115), (X(nx), ny, 0.097), 0.0032, seg=10)                     # needle bar
    p.cyl(ch, (X(nx), ny, 0.097), (X(nx), ny, 0.081), 0.0007, seg=6)                      # needle
    p.cyl(ch, (X(nx + 0.012), ny + 0.012, 0.115), (X(nx + 0.012), ny + 0.012, 0.088), 0.003, seg=10)   # presser bar
    p.box(ch, X(nx - 0.012), X(nx + 0.018), ny - 0.028, ny + 0.022, 0.0775, 0.0815, bevel=0.0012)   # presser foot
    p.box(ch, X(nx - 0.04), X(nx + 0.05), 0.04, 0.13, 0.075, 0.0765, bevel=0.0008)        # needle plate
    for k in range(3):
        p.box(dk, X(nx - 0.008 + k * 0.006), X(nx - 0.006 + k * 0.006), ny - 0.02, ny + 0.02, 0.0765, 0.0768)   # feed slots
    p.box(_acrylic("Sew_Bobbin_Cover", "#3A4048", 0.1, 0.6), X(nx + 0.055), X(nx + 0.11), 0.05, 0.12, 0.075, 0.0768,
          bevel=0.001)
    p.box(dk, X(0.02), X(w - 0.02), -0.0005, 0.0, 0.035, 0.037)                            # accessory-box seam
    sy, sz = d * 0.62, h + 0.018                                                           # horizontal spool on top
    p.cyl(ch, (X(w - 0.20), sy, sz), (X(w - 0.10), sy, sz), 0.003, seg=8)
    p.cyl(M["spools"][0], (X(w - 0.185), sy, sz), (X(w - 0.135), sy, sz), 0.017, seg=24)
    p.cyl(gry, (X(w - 0.135), sy, sz), (X(w - 0.128), sy, sz), 0.02, seg=24)              # spool cap
    p.box(gry, X(w - 0.08), X(w - 0.05), d * 0.5, d * 0.72, h - 0.002, h + 0.012, bevel=0.003)   # bobbin winder
    for x in (0.03, w - 0.03):
        for y in (0.03, d - 0.03):
            p.cyl(M["rubber"], (X(x), y, -0.004), (X(x), y, 0.0), 0.008, seg=10)
    return X(nx), ny


def sewing(w=0.42, d=0.20, h=0.30):
    """Brother computerised sewing machine (Innov-is style; branch 2026-11-26 remodel): moulded C-arm and bed with
    soft edges, grey arm panel, take-up lever, button row + speed slider, screen and keys on the pillar, hand wheel,
    needle bar, presser foot, needle plate with feed slots, smoked bobbin cover, horizontal spool on top. A quilting
    cotton piece is under the foot, half sewn (stitch line up to the needle)."""
    p = Part()
    nx, ny = _sew_body(p, 0.0, w, d, h)
    fab = mat("Fabric_Gingham", "#C7D9E8", 0.9)
    p.box(fab, nx - 0.13, nx + 0.06, ny - 0.17, ny + 0.06, 0.0766, 0.0776)
    for k in range(6):                                                                      # gingham checks
        p.box(mat("Fabric_Gingham_Dark", "#7FA6C7", 0.9), nx - 0.13 + k * 0.032, nx - 0.114 + k * 0.032, ny - 0.17,
              ny + 0.06, 0.0776, 0.0778)
    thread = mat("Thread_Red", "#C62828", 0.6)
    for k in range(14):                                                                     # straight stitch, done
        y = ny - 0.165 + k * 0.012
        if y > ny - 0.004:
            break
        p.box(thread, nx - 0.0008, nx + 0.0008, y, y + 0.007, 0.0778, 0.0782)
    return p


def embroidery(w=0.50, d=0.24, h=0.32):
    """Brother embroidery machine: the sewing body at the right with its embroidery unit clipped on the left; carriage
    arm holding a hoop under the needle; the hoop's fabric shows a Fab Lab hex badge part-embroidered (branch remodel)."""
    p = Part()
    bw = 0.36
    nx, ny = _sew_body(p, w - bw, bw, d - 0.03, h, screen_w=0.10)
    wh, gry, dk = M["white"], mat("Sew_Grey", "#B8BEC6", 0.4), M["dark"]
    _prism_xz(p, wh, _rounded_poly([(0, 0), (w - bw + 0.01, 0), (w - bw + 0.01, 0.07), (0, 0.07)], [0.01, 0, 0, 0.02]),
              0.10, d, bevel=0.006)                                                         # embroidery unit body
    p.box(gry, 0.02, w - bw - 0.02, 0.095, 0.11, 0.07, 0.072)                               # carriage track
    hx, hy = nx, ny - 0.01                                                                  # hoop centre under the needle
    p.box(gry, hx - 0.135, hx - 0.105, hy - 0.02, 0.13, 0.072, 0.086, bevel=0.003)          # carriage arm
    ring = _rounded_poly([(hx - 0.11, hy - 0.09), (hx + 0.07, hy - 0.09), (hx + 0.07, hy + 0.09), (hx - 0.11, hy + 0.09)],
                         [0.03] * 4)
    import bmesh
    # hoop: outer + inner frames as thin walls (boxes along the rounded outline)
    hoop = mat("Hoop_Grey", "#5F6670", 0.45)
    for a, b in zip(ring, ring[1:] + ring[:1]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L < 1e-5:
            continue
        mtx = Matrix.Translation(((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.081)) @ \
            Matrix.Rotation(math.atan2(b[1] - a[1], b[0] - a[0]), 4, "Z") @ Matrix.Diagonal((L + 0.004, 0.008, 0.01, 1))
        bmesh.ops.create_cube(p.bm(hoop), size=1.0, matrix=mtx)
    p.box(mat("Fabric_Linen", "#F1ECE2", 0.9), hx - 0.106, hx + 0.066, hy - 0.086, hy + 0.086, 0.0805, 0.0812)
    cols = ["#E53935", "#FBC02D", "#1E88E5", "#43A047"]
    cx, cy = hx - 0.02, hy                                                                  # hex badge, 3 of 4 colours done
    for i in range(7):
        a = math.pi / 6 + i * math.pi / 3
        if i == 6:
            px, py = cx, cy
        else:
            px, py = cx + 0.024 * math.cos(a), cy + 0.024 * math.sin(a)
        if i in (4, 5):
            continue                                                                         # not stitched yet
        p.cyl(mat(f"Thread_{cols[i % 3][1:]}", cols[i % 3], 0.5), (px, py, 0.0812), (px, py, 0.0822), 0.011, seg=6)
    for k in range(6):                                                                      # outline satin border
        a0, a1 = k * math.pi / 3, (k + 1) * math.pi / 3
        if k >= 4:
            continue
        x0_, y0_ = cx + 0.045 * math.cos(a0), cy + 0.045 * math.sin(a0)
        x1_, y1_ = cx + 0.045 * math.cos(a1), cy + 0.045 * math.sin(a1)
        L = math.hypot(x1_ - x0_, y1_ - y0_)
        mtx = Matrix.Translation(((x0_ + x1_) / 2, (y0_ + y1_) / 2, 0.0817)) @ \
            Matrix.Rotation(math.atan2(y1_ - y0_, x1_ - x0_), 4, "Z") @ Matrix.Diagonal((L, 0.004, 0.001, 1))
        bmesh.ops.create_cube(p.bm(mat("Thread_Black", "#202124", 0.5)), size=1.0, matrix=mtx)
    return p


def cricut(w=0.60, d=0.179, h=0.158, body=None):
    """Cricut Maker: rounded white body, lid open, grey mat feeding through the front.
    body: shell material (Maker 3 = pale blue, 538 x 178 x 151)."""
    p = Part()
    body = body or M["white"]
    p.box(body, 0, w, 0.03, d, 0, h * 0.75, bevel=0.035)
    p.box(M["grey"], 0.06, w - 0.06, 0.05, d - 0.03, h * 0.75 - 0.01, h * 0.75 + 0.005, bevel=0.004)   # carriage bay
    p.box(M["dark"], w * 0.35, w * 0.48, 0.07, 0.13, h * 0.75, h * 0.75 + 0.05, bevel=0.006)          # tool carriage
    p.box(body, 0.0, w, -0.11, -0.10, h * 0.75 - 0.005, h * 0.75 + 0.12, bevel=0.01)                # open lid
    p.box(M["mat_blue"], 0.03, w - 0.03, -0.22, d + 0.08, 0.035, 0.037)                               # cutting mat
    return p


def overlock(w=0.335, d=0.282, h=0.296):
    """Brother Lock M343D overlocker (335 x 282 x 296, Brother manual p. 34; branch 2026-11-26 remodel from product
    photos): moulded base with the narrow work plate on the left, body with the sloped front cover and the four tension
    dials in a recess on top, needle head left, hand wheel right, telescopic thread stand with its guide bar, four cones
    on pins behind; a fabric strip running through the knives."""
    p = Part()
    wh, gry, dk, ch = M["white"], mat("Sew_Grey", "#B8BEC6", 0.4), M["dark"], M["chrome"]
    _prism_xz(p, wh, _rounded_poly([(0, 0), (w, 0), (w, 0.07), (0.0, 0.07)], [0.01, 0.01, 0.02, 0.02]), 0.02, d - 0.02,
              bevel=0.006)                                                                  # base
    body = [(0.06, 0.07), (w - 0.01, 0.07), (w - 0.01, 0.22), (w - 0.06, 0.25), (0.10, 0.25), (0.06, 0.21)]
    _prism_xz(p, wh, _rounded_poly(body, [0, 0, 0.03, 0.04, 0.03, 0.02]), 0.04, d - 0.08, bevel=0.008)
    _prism_xz(p, gry, _rounded_poly([(0.13, 0.08), (w - 0.03, 0.08), (w - 0.03, 0.20), (0.13, 0.20)], [0.02] * 4),
              0.036, 0.04, bevel=0.002)                                                     # front looper cover
    p.box(dk, 0.13, w - 0.03, 0.0355, 0.036, 0.136, 0.138)                                  # cover seam
    for i in range(4):                                                                      # tension dials in a recess
        x = 0.13 + i * 0.038
        p.box(dk, x - 0.016, x + 0.016, 0.07, 0.10, 0.247, 0.251)
        c = "#7A1F3D"                                                                       # lab photo i-023: maroon
        p.cyl(mat(f"Ovl_Dial_{c[1:]}", c, 0.45), (x, 0.085, 0.24), (x, 0.085, 0.262), 0.014, seg=20)
    p.cyl(ch, (0.08, 0.07, 0.21), (0.08, 0.07, 0.11), 0.003, seg=8)                         # needle bar
    p.cyl(ch, (0.08, 0.07, 0.11), (0.08, 0.07, 0.085), 0.0007, seg=6)
    p.box(ch, 0.06, 0.10, 0.04, 0.10, 0.072, 0.076, bevel=0.001)                            # presser foot
    p.box(ch, 0.02, 0.13, 0.03, 0.12, 0.07, 0.0715)                                         # work plate
    p.cyl(wh, (w - 0.01, d * 0.45, 0.17), (w + 0.006, d * 0.45, 0.17), 0.05, seg=36)       # hand wheel
    p.cyl(gry, (w + 0.006, d * 0.45, 0.17), (w + 0.016, d * 0.45, 0.17), 0.047, seg=36)
    ty = d - 0.04                                                                           # thread stand
    p.box(gry, 0.04, w - 0.03, ty - 0.03, ty + 0.03, 0.07, 0.08, bevel=0.003)
    p.cyl(ch, (w / 2, ty, 0.08), (w / 2, ty, h * 1.75), 0.004, seg=10)                      # telescopic pole
    p.box(gry, 0.04, w - 0.04, ty - 0.008, ty + 0.008, h * 1.75, h * 1.75 + 0.012, bevel=0.003)   # guide bar
    for i in range(4):
        x = 0.07 + i * 0.065
        p.cyl(ch, (x, ty, 0.08), (x, ty, 0.20), 0.003, seg=8)                              # cone pins
        _cone(p, M["spools"][i], (x, ty, 0.085), (x, ty, 0.195), 0.030, 0.012, seg=24)      # thread cones
        p.cyl(ch, (x, ty - 0.004, h * 1.75 + 0.012), (x, ty - 0.004, h * 1.75 + 0.02), 0.004, seg=8)  # guide eyes
        th = mat(f"Ovl_Thread_{i}", "#EDEDED", 0.6)
        p.cyl(M["spools"][i], (x, ty, 0.195), (x, ty - 0.004, h * 1.75 + 0.012), 0.0004, seg=4)     # thread up
        p.cyl(M["spools"][i], (x, ty - 0.004, h * 1.75 + 0.012), (0.10 + i * 0.03, 0.10, 0.251), 0.0004, seg=4)
    p.box(mat("Fabric_Jersey", "#3F5E8C", 0.9), -0.10, 0.12, 0.05, 0.11, 0.0715, 0.0725)    # jersey strip through
    p.box(mat("Thread_White", "#F2F2F2", 0.6), -0.10, 0.08, 0.048, 0.056, 0.0725, 0.0735)   # overlocked edge
    for x in (0.03, w - 0.03):
        for y in (0.04, d - 0.04):
            p.cyl(M["rubber"], (x, y, -0.004), (x, y, 0.0), 0.009, seg=10)
    return p


def dust_collector(w=0.84, d=0.50, h=2.20):
    """ACword FT100 single-bag collector (lab photo i-012): grey stand, motor/impeller, white felt filter bag with the
    blue ACword band, blue clamp ring at the waist, clear lower chip bag about a third full of chips."""
    p = Part()
    cx = w / 2
    for x in (0.08, w - 0.12):
        for y in (0.08, d - 0.12):
            p.box(M["dark"], x, x + 0.04, y, y + 0.04, 0.0, 1.0)
    blue = mat("ACword_Blue", "#1F4FA8", 0.4)
    p.cyl(M["dark"], (cx, d / 2, 0.98), (cx, d / 2, 1.06), 0.27, seg=32)                       # ring
    p.cyl(blue, (cx, d / 2, 1.055), (cx, d / 2, 1.095), 0.247, seg=40)                        # clamp band
    p.cyl(M["grey"], (cx - 0.05, d / 2, 1.12), (cx + 0.30, d / 2, 1.12), 0.17, seg=28)         # motor
    p.cyl(M["grey"], (cx, -0.02, 1.12), (cx, d / 2, 1.12), 0.06, seg=20)                       # inlet
    p.cyl(M["felt"], (cx, d / 2, 1.06), (cx, d / 2, h - 0.06), 0.24, seg=40)                   # filter bag
    bmesh.ops.create_uvsphere(p.bm(M["felt"]), u_segments=40, v_segments=8, radius=0.24,
                              matrix=Matrix.Translation((cx, d / 2, h - 0.06)) @ Matrix.Scale(0.25, 4, (0, 0, 1)))
    for k in range(9):                                                                         # blue ACword band (front)
        a0 = math.radians(-24 + k * 6)                                                       # local -y = the front
        p.box(blue, cx + 0.2405 * math.sin(a0) - 0.013, cx + 0.2405 * math.sin(a0) + 0.013,
              d / 2 - 0.2405 * math.cos(a0) - 0.004, d / 2 - 0.2405 * math.cos(a0) + 0.004, 1.30, 1.72)
    clear = mat("ChipBag_Clear", "#DCE6EA", 0.12, coat=0.6)
    _b = next(n_ for n_ in clear.node_tree.nodes if n_.type == "BSDF_PRINCIPLED")
    _b.inputs["Alpha"].default_value = 0.28
    if hasattr(clear, "surface_render_method"):
        clear.surface_render_method = "BLENDED"
    p.cyl(clear, (cx, d / 2, 0.10), (cx, d / 2, 0.98), 0.24, seg=40)                           # clear chip bag
    chips = mat("Chips_Wood", "#C8A877", 0.95)
    _cone_mesh = lambda r0, r1, z0, z1: bmesh.ops.create_cone(p.bm(chips), cap_ends=True, segments=36, radius1=r0,
                                                               radius2=r1, depth=z1 - z0,
                                                               matrix=Matrix.Translation((cx, d / 2, (z0 + z1) / 2)))
    _cone_mesh(0.232, 0.225, 0.11, 0.36)                                                       # chips inside
    _cone_mesh(0.225, 0.12, 0.36, 0.42)
    return p

def control_box(w=0.50, d=0.30, h=0.70):
    p = Part()
    p.box(M["grey"], 0, w, 0, d, 0, h, bevel=0.01)
    p.box(M["red"], w * 0.4, w * 0.6, -0.02, 0.0, h * 0.75, h * 0.85, bevel=0.005)            # e-stop
    return p


def sheets(n, w, d, colors):
    """A stack of material sheets (ply + coloured acrylic)."""
    p = Part()
    z = 0.0
    for i in range(n):
        t = 0.006 if i % 2 else 0.003
        p.box(colors[i % len(colors)], 0, w, 0, d, z, z + t)
        z += t
    return p


def spool_stack(n):
    """Spare spools standing on edge in a row, facing the front."""
    p = Part()
    for i in range(n):
        spool_part(p, M["spools"][i % len(M["spools"])], 0.05 + i * 0.072, 0.06, 0.10, axis="x", width=0.062)
    return p


# ---------------------------------------------------------------- equipment-list machines added 2026-10-08
# (modelled from manufacturer/retailer photos listed in MACHINES.md; same simplified-but-recognisable style)
def _obox(p, m, center, size, rot):
    """Oriented box: size (sx, sy, sz) centred at `center`, rotated by the 3x3 matrix `rot`."""
    bmesh.ops.create_cube(p.bm(m), size=1.0, matrix=Matrix.Translation(center) @ rot.to_4x4()
                          @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)))


def _tube(p, m, pts, r, seg=12, step=0.01):
    """Smooth round tube along a Catmull-Rom path through pts (cables, feed tubes)."""
    def cr(p0, p1, p2, p3, t):
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    pts = [Vector(q) for q in pts]
    P = [pts[0]] + pts + [pts[-1]]
    dense = [cr(P[i - 1], P[i], P[i + 1], P[i + 2], k / 16) for i in range(1, len(P) - 2) for k in range(16)] + [pts[-1]]
    samples, acc, last = [dense[0]], 0.0, dense[0]
    for q in dense[1:]:
        acc += (q - last).length
        last = q
        if acc >= step:
            samples.append(q)
            acc = 0.0
    if (samples[-1] - pts[-1]).length > 1e-4:
        samples.append(pts[-1])
    bm, prev_n, rings = p.bm(m), None, []
    for i, c in enumerate(samples):
        t = (samples[min(i + 1, len(samples) - 1)] - samples[max(i - 1, 0)]).normalized()
        n = prev_n if prev_n is not None else (Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0)))
        n = (n - t * n.dot(t)).normalized()
        prev_n = n
        b = t.cross(n)
        rings.append([bm.verts.new(c + (n * math.cos(a) + b * math.sin(a)) * r) for a in (2 * math.pi * k / seg for k in range(seg))])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))


def creality_cr200b(w=0.411, d=0.435, h=0.503):
    """Creality CR-200B (411 x 435 x 503, enclosed; checked against Creality/All3DP photos): white body with a gloss
    black front bezel framing a big tinted door window, black lower front band with the CREALITY strip and the small
    touchscreen bottom right, rounded black-framed tinted windows in both white sides, clear acrylic top hood with a
    grey T-handle, small feet."""
    p = Part()
    gloss = mat("CR200_GlossBlack", "#0F1012", 0.12, coat=0.6)
    tint = _acrylic("CR200_Tint", "#1A1C1E", 0.05, 0.78)
    hood = _acrylic("Hood_Clear", "#DCE6EA", 0.05, 0.22)
    hb = 0.405                                                           # body height under the hood
    for x in (0.04, w - 0.04):
        for y in (0.04, d - 0.04):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.010), 0.014, seg=12)
    p.box(M["white"], 0.0, w, 0.015, d, 0.010, hb, bevel=0.014)                      # white shell
    p.box(gloss, 0.0, w, 0.0, 0.022, 0.010, hb, bevel=0.012)                         # black front bezel
    p.box(tint, 0.030, w - 0.030, -0.002, 0.0, 0.105, hb - 0.030, bevel=0.002)       # door window
    p.box(M["dark"], 0.030, w - 0.030, 0.10, d - 0.03, 0.098, 0.104)                 # bed level inside (dark)
    p.box(M["chrome"], 0.035, 0.095, -0.0015, 0.0, 0.088, 0.092)                     # CREALITY strip
    p.box(M["lcd"], w - 0.115, w - 0.050, -0.0025, -0.0005, 0.030, 0.080)            # touchscreen
    for x in (-0.002, w):                                                            # side windows, black surround
        p.box(gloss, x, x + 0.002, 0.075, d - 0.050, 0.110, hb - 0.040, bevel=0.0008)
        p.box(tint, x - 0.0005 if x < 0 else x + 0.0005, x + 0.0015 if x < 0 else x + 0.0025, 0.085, d - 0.060,
              0.120, hb - 0.050)
    p.box(M["black"], w - 0.002, w + 0.004, 0.10, 0.13, 0.035, 0.050)               # USB/SD on the right side
    p.box(hood, 0.050, w - 0.050, 0.030, d - 0.060, hb, h - 0.004, bevel=0.010)      # clear top hood
    p.box(M["grey"], w * 0.5 - 0.004, w * 0.5 + 0.004, 0.026, 0.030, hb + 0.020, h - 0.020)   # T-handle stem
    p.box(M["grey"], w * 0.5 - 0.045, w * 0.5 + 0.045, 0.026, 0.030, h - 0.026, h - 0.016)    # T-handle bar
    p.cyl(M["dark"], (w + 0.0, d * 0.75, 0.30), (w + 0.03, d * 0.75, 0.30), 0.008, seg=10)  # spool-holder stub
    return p


def flashforge_ad5m_pro(w=0.380, d=0.400, h=0.453):
    """Flashforge Adventurer 5M Pro (380 x 400 x 453; checked against Flashforge photos): charcoal enclosure with
    rounded vertical edges, top band with the 4.3" touchscreen and power knob (top right), thin silver line under the
    band, full-width tinted glass door, white FLASHFORGE mark low on the door, smoked glass top."""
    p = Part()
    body = mat("FF_Charcoal", "#26282B", 0.42, coat=0.15)
    tint = _acrylic("FF_DoorTint", "#202326", 0.05, 0.80)
    zb = h - 0.080
    p.box(body, 0.0, w, 0.0, d, 0.008, h, bevel=0.022)
    p.box(tint, 0.022, w - 0.022, -0.002, 0.0, 0.030, zb - 0.006, bevel=0.002)       # door glass
    p.box(M["chrome"], 0.015, w - 0.015, -0.0015, 0.0, zb - 0.004, zb - 0.002)       # silver line
    p.box(M["lcd"], w - 0.165, w - 0.075, -0.0025, -0.0005, zb + 0.012, zb + 0.066)  # touchscreen
    p.cyl(M["black"], (w - 0.040, -0.004, zb + 0.050), (w - 0.040, 0.0, zb + 0.050), 0.011, seg=20)   # knob
    p.box(M["white"], w * 0.30, w * 0.70, -0.0025, -0.0015, 0.050, 0.060)            # FLASHFORGE mark
    p.box(M["pei"], 0.06, w - 0.06, 0.06, d - 0.08, 0.10, 0.106)                     # build plate behind glass
    p.box(M["smoke"], 0.03, w - 0.03, 0.03, d - 0.03, h, h + 0.003)                  # smoked top glass
    for x in (0.04, w - 0.04):
        for y in (0.04, d - 0.04):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.008), 0.014, seg=12)
    return p


def creality_cr10_max(w=0.65, d=0.785, h=0.735):
    """Creality CR-10 Max (650 x 785 x 735; checked against product photos): black 2040 extrusion base, big
    450 x 450 bed with a black coated plate, black control box front right with the touchscreen, twin 2040 uprights
    and top bar, X gantry with RED aluminium brackets, red/black hotend carriage with fan, diagonal support rods from
    the top of the uprights to the rear of the base, spool on the top bar."""
    p = Part()
    red = mat("CR10_Red", "#C41E2A", 0.35, metal=0.4)
    alu = M["alu"]
    for x in (0.02, w - 0.06):                                                        # base rails (y)
        p.box(alu, x, x + 0.04, 0.04, d - 0.03, 0.035, 0.075, bevel=0.002)
    for y in (0.04, d - 0.07):                                                        # base cross members
        p.box(alu, 0.02, w - 0.02, y, y + 0.04, 0.035, 0.055, bevel=0.002)
    for x in (0.04, w - 0.04):
        for y in (0.06, d - 0.05):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.035), 0.022, seg=16)            # feet
    yb = 0.07                                                                         # bed front
    p.box(alu, 0.11, w - 0.11, yb + 0.05, yb + 0.42, 0.080, 0.090)                    # Y carriage
    p.box(M["alusatin"] if "alusatin" in M else M["chrome"], 0.095, w - 0.095, yb, yb + 0.47, 0.100, 0.108)  # bed
    p.box(M["pei"], 0.100, w - 0.100, yb + 0.005, yb + 0.465, 0.108, 0.110)          # coated plate
    p.box(M["white"], w * 0.40, w * 0.60, yb + 0.43, yb + 0.45, 0.1101, 0.1103)      # CREALITY print on the plate
    p.box(M["black"], w - 0.33, w - 0.03, -0.04, 0.17, 0.035, 0.105, bevel=0.006)    # control box
    p.box(M["lcd"], w - 0.25, w - 0.12, -0.0415, -0.0395, 0.050, 0.095)              # touchscreen
    p.box(M["white"], w - 0.32, w - 0.27, -0.0415, -0.0395, 0.068, 0.076)            # CREALITY label
    yu = 0.52                                                                          # upright plane
    for x in (0.02, w - 0.06):
        p.box(alu, x, x + 0.04, yu, yu + 0.02, 0.075, h - 0.04, bevel=0.002)          # 2040 uprights
        p.box(M["black"], x - 0.005, x + 0.045, yu + 0.02, yu + 0.065, 0.075, 0.12, bevel=0.003)   # Z motors
        rod_top, rod_bot = Vector((x + 0.02, yu + 0.02, h - 0.06)), Vector((x + 0.02, d - 0.04, 0.075))
        p.cyl(alu, rod_top, rod_bot, 0.009, seg=12)                                   # support rod to the rear
        p.cyl(M["brass"], (x + 0.02, yu - 0.015, 0.12), (x + 0.02, yu - 0.015, h - 0.06), 0.004, seg=8)   # leadscrew
    p.box(alu, 0.02, w - 0.02, yu, yu + 0.02, h - 0.04, h, bevel=0.002)               # top bar
    zx = 0.47                                                                          # gantry height
    p.box(alu, 0.06, w - 0.06, yu - 0.035, yu - 0.015, zx, zx + 0.04, bevel=0.002)   # X extrusion
    for x0 in (0.0, w - 0.09):                                                         # red gantry brackets
        p.box(red, x0, x0 + 0.09, yu - 0.045, yu - 0.035, zx - 0.05, zx + 0.08, bevel=0.003)
    p.box(M["black"], 0.0, 0.05, yu - 0.10, yu - 0.045, zx - 0.02, zx + 0.035, bevel=0.003)   # X motor
    hx = w * 0.42
    p.box(red, hx, hx + 0.08, yu - 0.050, yu - 0.040, zx - 0.04, zx + 0.07, bevel=0.003)   # carriage plate
    p.box(M["black"], hx + 0.005, hx + 0.075, yu - 0.110, yu - 0.050, zx - 0.05, zx + 0.05, bevel=0.006)  # hotend shroud
    for k in range(3):                                                                 # fan grille
        p.cyl(M["dark"], (hx + 0.04, yu - 0.1105, zx), (hx + 0.04, yu - 0.1101, zx), 0.008 + k * 0.007, seg=20)
    p.box(M["black"], hx + 0.015, hx + 0.065, yu - 0.09, yu - 0.05, zx + 0.07, zx + 0.11, bevel=0.003)   # extruder
    p.cyl(M["brass"], (hx + 0.04, yu - 0.08, zx - 0.05), (hx + 0.04, yu - 0.08, zx - 0.07), 0.004, seg=10)
    _tube(p, M["black"], [(hx + 0.04, yu - 0.07, zx + 0.11), (hx + 0.06, yu - 0.03, zx + 0.20), (w * 0.5, yu + 0.01, h + 0.02)], 0.009)
    p.box(M["black"], w * 0.5 - 0.012, w * 0.5 + 0.012, yu - 0.005, yu + 0.05, h, h + 0.06, bevel=0.003)  # spool arm
    spool_part(p, M["spools"][7], w * 0.5, yu + 0.06, h + 0.105)
    return p


def eazao_zero(w=0.35, d=0.30, h=0.50):
    """Eazao Zero clay printer (350 x 300 x 500 frame; checked against Eazao photos): white base with the screen
    front right, white tower on the right carrying the white X arm, square white bed, extruder = stepper on a clear
    auger barrel with a dark-green nozzle, aluminium push-rod clay cartridge with its stepper on the left, clear
    feed tube arching from the cartridge up to the extruder, a twisted clay vase on the bed."""
    p = Part()
    wh = M["white"]
    clay = mat("Clay_Raw", "#D8CBB6", 0.92)
    tube = _acrylic("Feed_Tube", "#E8EEF0", 0.05, 0.35)
    for x in (0.08, w - 0.03):
        for y in (0.03, d - 0.03):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.010), 0.012, seg=12)
    p.box(wh, 0.05, w, 0.0, d, 0.010, 0.125, bevel=0.010)                           # base
    p.box(mat("Eazao_Screen", "#141A1E", 0.15, emit=0.3), w - 0.115, w - 0.035, -0.0015, 0.0, 0.035, 0.095)
    p.box(wh, w - 0.085, w, 0.06, d, 0.125, h, bevel=0.008)                         # tower
    p.box(M["dark"], w - 0.086, w - 0.084, 0.10, d - 0.03, 0.20, h - 0.05)          # Z slot (tower face)
    p.box(M["black"], w - 0.082, w - 0.080, 0.08, 0.16, h - 0.10, h - 0.085)        # "eazao" mark
    p.box(M["dark"], 0.10, 0.27, 0.06, 0.24, 0.125, 0.135)                          # Y carriage
    p.box(wh, 0.085, 0.285, 0.050, 0.250, 0.135, 0.150, bevel=0.004)                # bed
    za = 0.335                                                                        # X arm
    p.box(wh, 0.12, w - 0.085, 0.10, 0.16, za, za + 0.045, bevel=0.006)
    ex, ey = 0.185, 0.105
    p.box(wh, ex - 0.03, ex + 0.03, ey - 0.035, ey + 0.035, za - 0.010, za + 0.050, bevel=0.004)   # carriage
    p.cyl(tube, (ex, ey - 0.045, za - 0.06), (ex, ey - 0.045, za + 0.07), 0.016, seg=20)           # auger barrel
    p.cyl(M["gold"], (ex, ey - 0.045, za - 0.05), (ex, ey - 0.045, za + 0.06), 0.006, seg=12)      # auger
    p.box(M["black"], ex - 0.021, ex + 0.021, ey - 0.066, ey - 0.024, za + 0.07, za + 0.112, bevel=0.003)  # stepper
    p.cyl(mat("Eazao_Nozzle", "#2F5B3B", 0.45), (ex, ey - 0.045, za - 0.06), (ex, ey - 0.045, za - 0.095), 0.006, seg=12)
    p.cyl(M["dark"], (ex + 0.02, ey - 0.045, za + 0.03), (ex + 0.03, ey - 0.045, za + 0.03), 0.006, seg=10)  # blue fitting
    # clay cartridge (push rod) on the left, rising to the rear motor
    a, b = Vector((-0.17, 0.035, 0.06)), Vector((0.03, 0.12, 0.10))
    p.cyl(M["alusatin"] if "alusatin" in M else M["chrome"], a, b, 0.032, seg=24)
    p.box(M["black"], 0.02, 0.07, 0.09, 0.15, 0.070, 0.135, bevel=0.003)             # cartridge stepper/gearbox
    p.box(M["grey"], -0.20, -0.165, 0.015, 0.055, 0.0, 0.10, bevel=0.003)           # front bracket on the bench
    p.cyl(mat("Fitting_Blue", "#2C6FD1", 0.4), a - Vector((0.012, 0, 0)), a + Vector((0.004, 0, 0)), 0.014, seg=14)
    _tube(p, tube, [a - Vector((0.02, 0.0, 0.0)), Vector((-0.10, 0.02, 0.32)), Vector((0.03, 0.04, 0.44)),
                    Vector((ex + 0.03, ey - 0.045, za + 0.03))], 0.006)
    # twisted clay vase (stacked rotated squares)
    vx, vy, z = 0.185, 0.150, 0.150
    for k in range(18):
        s = 0.045 + 0.018 * math.sin(k / 17 * math.pi)
        _obox(p, clay, Vector((vx, vy, z + 0.0035)), (s, s, 0.0072), Matrix.Rotation(k * 0.09, 3, "Z"))
        z += 0.0072
    return p


def revopoint_pop3_kit():
    """Handheld 3D scanner kit (the lab's is "just a handheld scanner"; Revopoint POP 3 as the stand-in, 153 x 45 x 29
    head; checked against Revopoint/retailer photos): dark-grey aluminium head with a black glass face (two IR
    cameras, projector, RGB camera, LEDs) on a black mini tripod/handle, a small black turntable with a blue printed
    figure, and the grey zip carry case lying open-lid beside it."""
    p = Part()
    alu = mat("Scanner_Alu", "#55595E", 0.30, metal=0.7)
    glass = mat("Scanner_Glass", "#0B0C0E", 0.08, coat=0.8)
    blk = mat("Scanner_Black", "#16171A", 0.45)
    felt = mat("Case_Grey", "#6B6E72", 0.9)
    # tripod: three splayed legs, column, ball head
    c = Vector((0.12, 0.10, 0.0))
    for k in range(3):
        a_ = math.radians(90 + k * 120)
        foot = c + Vector((math.cos(a_) * 0.075, math.sin(a_) * 0.075, 0.004))
        p.cyl(blk, foot, c + Vector((0, 0, 0.075)), 0.008, seg=10)
    p.cyl(blk, c + Vector((0, 0, 0.06)), c + Vector((0, 0, 0.145)), 0.014, seg=16)
    bmesh.ops.create_uvsphere(p.bm(blk), u_segments=14, v_segments=8, radius=0.012,
                              matrix=Matrix.Translation(c + Vector((0, 0, 0.152))))
    hc = c + Vector((0, 0, 0.162 + 0.0225))                                         # head centre, face toward -y
    tilt = Matrix.Rotation(-0.25, 3, "X")
    _obox(p, alu, hc, (0.153, 0.029, 0.045), tilt)
    face = hc + tilt @ Vector((0, -0.0148, 0))
    _obox(p, glass, face, (0.143, 0.002, 0.036), tilt)
    for dx, r, m_ in ((-0.055, 0.0065, M["smoke"]), (-0.035, 0.003, M["lcd"]), (0.0, 0.0055, M["smoke"]),
                      (0.035, 0.003, M["lcd"]), (0.055, 0.0065, M["smoke"])):
        q = face + tilt @ Vector((dx, -0.0012, 0))
        p.cyl(m_, q, q + tilt @ Vector((0, -0.0008, 0)), r, seg=16)
    # turntable + figure
    t = Vector((0.31, 0.10, 0.0))
    p.cyl(blk, t, t + Vector((0, 0, 0.030)), 0.075, seg=36)
    p.cyl(M["dark"], t + Vector((0, 0, 0.030)), t + Vector((0, 0, 0.036)), 0.070, seg=36)
    fig = M["spools"][2]
    for z0, z1, r in ((0.036, 0.075, 0.016), (0.075, 0.115, 0.022), (0.115, 0.13, 0.010)):
        p.cyl(fig, t + Vector((0, 0, z0)), t + Vector((0, 0, z1)), r, seg=16)
    bmesh.ops.create_uvsphere(p.bm(fig), u_segments=14, v_segments=8, radius=0.017, matrix=Matrix.Translation(t + Vector((0, 0, 0.145))))
    # carry case, closed, at the back
    p.box(felt, 0.02, 0.36, 0.22, 0.40, 0.0, 0.085, bevel=0.02)
    p.box(M["black"], 0.15, 0.23, 0.215, 0.225, 0.07, 0.08, bevel=0.003)           # handle
    return p


def loklik_auto_press(w=0.50, d=0.40, h=0.30, color="#47C3C9"):
    """LOKLiK Auto Heat Press 15 x 15" (500 x 400 x 300, 38 x 38 cm plate; checked against LOKLiK product photos):
    gloss teal base tray with the black pull-out drawer + handle, black lower platen, wide gloss-teal upper hood with a
    black skirt, raised teal control box on top (ribbed top, black display, white buttons), LOKLiK mark on the base."""
    p = Part()
    teal = mat("Loklik_Teal", color, 0.18, coat=0.6)
    blk = mat("Loklik_Black", "#18191B", 0.4)
    p.box(teal, 0.0, w, 0.0, d, 0.0, 0.055, bevel=0.018)                            # base tray
    p.box(blk, 0.13, w - 0.13, -0.004, d - 0.06, 0.04, 0.115, bevel=0.006)          # drawer body
    p.box(blk, 0.18, w - 0.18, -0.020, -0.004, 0.065, 0.085, bevel=0.005)           # drawer handle
    p.box(blk, 0.02, w - 0.02, 0.0, d - 0.03, 0.115, 0.140, bevel=0.008)            # lower platen
    p.box(blk, 0.015, w - 0.015, -0.005, d - 0.02, 0.150, 0.165, bevel=0.006)       # hood skirt
    p.box(teal, 0.010, w - 0.010, -0.010, d - 0.015, 0.165, 0.215, bevel=0.02)      # upper hood
    p.box(blk, w * 0.32, w * 0.68, 0.10, d - 0.06, 0.215, 0.225)                     # neck
    p.box(teal, w * 0.29, w * 0.71, 0.08, d - 0.04, 0.225, h, bevel=0.012)          # control box
    for k in range(12):                                                               # ribbed top
        y = 0.10 + k * (d - 0.16) / 11
        p.box(teal, w * 0.30, w * 0.70, y, y + 0.006, h, h + 0.002)
    p.box(mat("Loklik_LCD", "#0B0B0C", 0.15, emit=0.0), w * 0.43, w * 0.57, 0.0785, 0.08, 0.255, 0.280)
    p.box(M["lcd"], w * 0.445, w * 0.555, 0.0780, 0.0785, 0.260, 0.275)
    for dx in (-0.075, -0.055, 0.055, 0.075):                                          # white buttons
        p.cyl(M["white"], (w / 2 + dx, 0.0785, 0.265), (w / 2 + dx, 0.074, 0.265), 0.008, seg=14)
    p.box(M["grey"], w * 0.42, w * 0.58, -0.0005, 0.0, 0.018, 0.030)                  # LOKLiK mark
    return p


def secabo_tc7(w=0.43, d=0.57, open_deg=24):
    """Classic red industrial clamshell heat press (the lab's exact model unknown; modelled on the Secabo TC7 40 x 50,
    43 x 57 x 75 closed; checked against Secabo photos), shown open:
    black steel base on levelling feet, galvanised lower platen frame with the black silicone pad, red vented heat
    hood on a black heat plate hinged at the back, black lever arms up to the foam handle, red controller with LCD
    and buttons on the rear right."""
    p = Part()
    red = mat("Secabo_Red", "#E2361F", 0.40, coat=0.2)
    blk = mat("Secabo_Black", "#141414", 0.45, metal=0.3)
    pad = mat("Silicone_Pad", "#1E1E1F", 0.85)
    for x in (0.05, w - 0.05):                                                       # base runners + feet
        p.box(blk, x - 0.02, x + 0.02, 0.06, d - 0.02, 0.020, 0.045, bevel=0.003)
        for y in (0.08, d - 0.05):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.020), 0.018, seg=12)
    p.box(blk, w / 2 - 0.12, w / 2 + 0.12, 0.10, 0.40, 0.045, 0.075)               # cross plate
    p.box(M["galv"], 0.0, w, 0.0, 0.50, 0.075, 0.105, bevel=0.003)                  # lower platen frame
    p.box(pad, 0.012, w - 0.012, 0.012, 0.488, 0.105, 0.118, bevel=0.003)           # silicone pad
    p.box(blk, w / 2 - 0.07, w / 2 + 0.07, 0.47, d, 0.045, 0.40, bevel=0.004)       # rear column
    hinge = Vector((w / 2, 0.50, 0.33))
    R = Matrix.Rotation(-math.radians(open_deg), 3, "X")                             # opens upward at the front
    def hp(loc):                                                                     # hood point (closed frame -> open)
        return hinge + R @ (Vector(loc) - hinge)
    _obox(p, blk, hp((w / 2, 0.25, 0.135)), (0.42, 0.50, 0.012), R)                # heat plate
    _obox(p, red, hp((w / 2, 0.25, 0.168)), (0.43, 0.51, 0.055), R)                # red vented hood
    for k in range(26):                                                             # vent slots, front + sides
        x = 0.025 + k * (w - 0.05) / 25
        _obox(p, M["black"], hp((x, -0.0055, 0.168)), (0.006, 0.002, 0.034), R)
    for k in range(18):
        y = 0.03 + k * 0.44 / 17
        for x in (-0.0055, w + 0.0055):
            _obox(p, M["black"], hp((x, y, 0.168)), (0.002, 0.006, 0.034), R)
    _obox(p, mat("Safety_Yellow", "#F2C200", 0.4), hp((w - 0.05, -0.006, 0.170)), (0.03, 0.002, 0.026), R)
    _obox(p, blk, hp((w / 2, 0.47, 0.215)), (0.10, 0.08, 0.06), R)                 # hood mount block
    for x in (w / 2 - 0.06, w / 2 + 0.06):                                          # lever arms + handle
        p.cyl(blk, (x, 0.50, 0.30), (x, 0.40, 0.80), 0.012, seg=10)
    p.cyl(blk, (w / 2 - 0.06, 0.40, 0.80), (w / 2 + 0.06, 0.40, 0.80), 0.012, seg=10)
    p.cyl(mat("Foam_Grip", "#202020", 0.9), (w / 2 - 0.09, 0.39, 0.83), (w / 2 + 0.09, 0.39, 0.83), 0.022, seg=16)
    p.cyl(blk, (w / 2 - 0.06, 0.40, 0.80), (w / 2 - 0.06, 0.39, 0.83), 0.010, seg=8)
    p.cyl(blk, (w / 2 + 0.06, 0.40, 0.80), (w / 2 + 0.06, 0.39, 0.83), 0.010, seg=8)
    p.box(red, w - 0.17, w - 0.01, 0.50, 0.56, 0.36, 0.53, bevel=0.006)            # controller
    p.box(mat("Secabo_LCD", "#0E1A24", 0.15, emit=0.6), w - 0.155, w - 0.025, 0.4985, 0.50, 0.44, 0.515)
    for i in range(4):
        p.box(M["dark"], w - 0.155 + i * 0.035, w - 0.13 + i * 0.035, 0.4985, 0.50, 0.385, 0.40)
    _tube(p, M["black"], [(w - 0.03, 0.56, 0.40), (w + 0.02, 0.60, 0.30), (w - 0.02, 0.56, 0.20)], 0.006)
    return p


def cricut_easypress3(w=0.305, d=0.254, on_base=True):
    """Cricut EasyPress 3, 12 x 10" (checked against Cricut photos): pale blue-grey shell with the integrated arch
    handle, small display on top, black heat-plate skirt; resting on its grey safety base."""
    p = Part()
    blue = mat("Cricut_PaleBlue", "#B9C9D8", 0.35, coat=0.2)
    z0 = 0.0
    if on_base:
        p.box(mat("Cricut_SafetyBase", "#8E979F", 0.5), -0.02, w + 0.02, -0.02, d + 0.02, 0.0, 0.014, bevel=0.006)
        z0 = 0.014
    p.box(M["black"], -0.004, w + 0.004, -0.004, d + 0.004, z0, z0 + 0.016, bevel=0.006)   # plate skirt
    p.box(blue, 0.0, w, 0.0, d, z0 + 0.016, z0 + 0.055, bevel=0.020)                       # shell
    p.box(blue, 0.055, w - 0.055, 0.045, d - 0.045, z0 + 0.055, z0 + 0.105, bevel=0.022)   # arch handle
    p.box(M["dark"], 0.075, w - 0.075, -0.001, d * 0.62, z0 + 0.058, z0 + 0.082)            # finger opening
    p.box(M["black"], w * 0.38, w * 0.62, d - 0.06, d - 0.03, z0 + 0.0551, z0 + 0.0557)     # display
    p.box(M["lcd"], w * 0.42, w * 0.58, d - 0.055, d - 0.035, z0 + 0.0557, z0 + 0.0560)
    return p


def cricut_mug_press(w=0.275, d=0.157, h=0.165):
    """Cricut Mug Press (275 x 157 x 165; checked against Cricut photos): white rounded body, mint-green translucent
    heating-sleeve window on the left, mug slot in the top; a sublimated mug stands beside it."""
    p = Part()
    mint = _acrylic("Mug_Mint", "#9FD9C6", 0.1, 0.75)
    p.box(M["white"], 0.0, w, 0.0, d, 0.0, h, bevel=0.028)
    p.box(mint, 0.030, 0.115, -0.002, 0.0, 0.020, h - 0.010, bevel=0.004)          # sleeve window
    p.box(M["dark"], 0.030, 0.115, 0.025, d - 0.025, h - 0.0005, h + 0.0005)        # mug slot (top)
    p.box(M["grey"], w - 0.10, w - 0.04, -0.001, 0.0, h * 0.45, h * 0.52)           # cricut wordmark
    mc = Vector((w + 0.06, d * 0.5, 0.0))                                            # mug beside it
    p.cyl(M["white"], mc, mc + Vector((0, 0, 0.096)), 0.041, seg=32)
    p.cyl(M["spools"][2], mc + Vector((0, 0, 0.02)), mc + Vector((0, 0, 0.08)), 0.0415, seg=32)  # printed band
    p.cyl(M["dark"], mc + Vector((0, 0, 0.0955)), mc + Vector((0, 0, 0.0962)), 0.036, seg=24)
    p.box(M["white"], mc.x + 0.040, mc.x + 0.058, mc.y - 0.005, mc.y + 0.005, 0.025, 0.075, bevel=0.004)  # handle
    return p


def bekant_cart(w=0.61, d=0.45, h=1.01):
    """IKEA BEKANT storage unit on castors, mesh black (61 x 45 x 101; checked against IKEA photos) - the lab's
    rolling carts, hacked with a birch-ply top as the equipment list suggests: perforated black steel sides and back,
    black poles, black-stained shelves, bottom drawer with a top grip, castors."""
    p = Part()
    mesh = _perforated("Bekant_Mesh")
    ash = mat("Bekant_BlackAsh", "#1C1B1A", 0.55)
    zb = 0.085                                                                      # body bottom above castors
    for x in (0.0, w - 0.025):
        for y in (0.0, d - 0.025):
            p.box(M["black"], x, x + 0.025, y, y + 0.025, zb, h - 0.02, bevel=0.008)     # poles
    for x in (0.0, w - 0.002):
        p.box(mesh, x, x + 0.002, 0.025, d - 0.025, zb + 0.01, h - 0.025)        # mesh sides
    p.box(mesh, 0.025, w - 0.025, d - 0.003, d - 0.001, zb + 0.01, h - 0.025)    # mesh back
    p.box(ash, 0.0, w, 0.0, d, h - 0.02, h, bevel=0.004)                           # top
    p.box(ash, 0.004, w - 0.004, 0.004, d - 0.004, zb, zb + 0.02)                  # bottom
    for zs in (0.43, 0.68):
        p.box(ash, 0.004, w - 0.004, 0.01, d - 0.01, zs, zs + 0.018)               # shelves
    p.box(ash, 0.006, w - 0.006, -0.004, 0.012, zb + 0.02, 0.41, bevel=0.003)      # drawer front
    p.box(M["black"], 0.03, w - 0.03, -0.012, 0.0, 0.385, 0.398, bevel=0.004)      # grip lip
    p.box(M["black"], w * 0.5 - 0.004, w * 0.5 + 0.004, 0.04, d - 0.04, h * 0.5, h * 0.62)   # inner divider pole
    for x in (0.05, w - 0.05):
        for y in (0.05, d - 0.05):
            p.cyl(M["black"], (x, y, zb), (x, y, 0.07), 0.008, seg=10)
            p.cyl(M["rubber"], (x - 0.012, y, 0.035), (x + 0.012, y, 0.035), 0.035, seg=20)
    p.box(lib_ply(), -0.01, w + 0.01, -0.01, d + 0.01, h, h + 0.018, bevel=0.002)  # birch-ply top (the "hack")
    return p


def lib_ply():
    return bpy.data.materials.get("Plywood_Birch") or mat("Plywood_Birch", "#E0C9A2", 0.5)


def _perforated(name, pitch=0.008, hole=0.0042, hexcol="#141414"):
    """Black perforated steel (round holes on a square grid, cut out with alpha), mapped on the face plane."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes.new, nt.links.new
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = 0.5
    b.inputs["Metallic"].default_value = 0.4
    geo = N("ShaderNodeNewGeometry")
    tc = N("ShaderNodeTexCoord")
    sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Object"], sep.inputs[0])
    sn = N("ShaderNodeSeparateXYZ"); L(geo.outputs["Normal"], sn.inputs[0])
    ax = N("ShaderNodeMath"); ax.operation = "ABSOLUTE"; L(sn.outputs["X"], ax.inputs[0])
    sel = N("ShaderNodeMath"); sel.operation = "GREATER_THAN"; sel.inputs[1].default_value = 0.5; L(ax.outputs[0], sel.inputs[0])
    mixu = N("ShaderNodeMix"); mixu.data_type = "FLOAT"                    # u = y on x-facing panels, else x
    L(sel.outputs[0], mixu.inputs["Factor"]); L(sep.outputs["X"], mixu.inputs["A"]); L(sep.outputs["Y"], mixu.inputs["B"])
    def cell(src):
        mu = N("ShaderNodeMath"); mu.operation = "MULTIPLY"; mu.inputs[1].default_value = 1.0 / pitch; L(src, mu.inputs[0])
        fr = N("ShaderNodeMath"); fr.operation = "FRACT"; L(mu.outputs[0], fr.inputs[0])
        sb = N("ShaderNodeMath"); sb.operation = "SUBTRACT"; sb.inputs[1].default_value = 0.5; L(fr.outputs[0], sb.inputs[0])
        sq = N("ShaderNodeMath"); sq.operation = "MULTIPLY"; L(sb.outputs[0], sq.inputs[0]); L(sb.outputs[0], sq.inputs[1])
        return sq
    a, c = cell(mixu.outputs["Result"]), cell(sep.outputs["Z"])
    add = N("ShaderNodeMath"); add.operation = "ADD"; L(a.outputs[0], add.inputs[0]); L(c.outputs[0], add.inputs[1])
    gt = N("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = (hole / pitch / 2) ** 2
    L(add.outputs[0], gt.inputs[0])
    L(gt.outputs[0], b.inputs["Alpha"])
    m.diffuse_color = lin(hexcol)
    return m


def microwave(w=0.45, d=0.35, h=0.26):
    """Compact white microwave (clay prep, per the equipment list): door with dark window, control strip right."""
    p = Part()
    p.box(M["white"], 0.0, w, 0.0, d, 0.0, h, bevel=0.012)
    p.box(M["smoke"], 0.03, w - 0.13, -0.002, 0.0, 0.04, h - 0.04, bevel=0.004)
    p.box(M["grey"], w - 0.11, w - 0.02, -0.002, 0.0, 0.03, h - 0.03, bevel=0.003)
    p.box(M["lcd"], w - 0.095, w - 0.035, -0.0035, -0.002, h - 0.075, h - 0.05)
    return p


def clay_bucket(r=0.14, h=0.24):
    p = Part()
    p.cyl(M["white"], (0, 0, 0), (0, 0, h), r, seg=32)
    p.cyl(M["grey"], (0, 0, h), (0, 0, h + 0.015), r + 0.008, seg=32)
    return p


# ---------------------------------------------------------------- placement helpers
FACE = {"-x": -math.pi / 2, "+x": math.pi / 2, "-y": 0.0, "+y": math.pi}   # rotation so local front (-y) faces this way


def place(part, name, col, cx, cy, z, w, d, facing):
    """Centre a w x d footprint at (cx, cy) on height z, front facing `facing`."""
    rot = FACE[facing]
    off = Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0))
    return part.emit(name, col, Vector((cx, cy, z)) + off, rot)


def exhaust(col, name, pts, r=0.05):
    p = Part()
    for a, b in zip(pts, pts[1:]):
        p.cyl(M["galv"], a, b, r, seg=20)
    for q in pts[1:-1]:
        bmesh.ops.create_uvsphere(p.bm(M["galv"]), u_segments=20, v_segments=10, radius=r, matrix=Matrix.Translation(q))
    return p.emit(name, col, Vector((0, 0, 0)), 0.0)


def ribbed_hose(m, pts, r, pitch=0.014, seg=16):
    """Corrugated hose along a Catmull-Rom path through pts: real ribs (radius alternates every pitch/2)."""
    def cr(p0, p1, p2, p3, t):
        return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    P = [pts[0]] + list(pts) + [pts[-1]]
    dense = []
    for i in range(1, len(P) - 2):
        for k in range(20):
            dense.append(cr(P[i - 1], P[i], P[i + 1], P[i + 2], k / 20))
    dense.append(pts[-1])
    samples, acc, last = [dense[0]], 0.0, dense[0]                      # resample at half-pitch spacing
    for q in dense[1:]:
        acc += (q - last).length
        last = q
        if acc >= pitch / 2:
            samples.append(q)
            acc = 0.0
    p = Part()
    bm = p.bm(m)
    prev_n, rings = None, []
    for i, c in enumerate(samples):
        t = (samples[min(i + 1, len(samples) - 1)] - samples[max(i - 1, 0)]).normalized()
        n = prev_n if prev_n is not None else (Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0)))
        n = (n - t * n.dot(t)).normalized()                             # parallel transport
        prev_n = n
        b = t.cross(n)
        rr = r if i % 2 == 0 else r * 0.90
        rings.append([bm.verts.new(c + (n * math.cos(a) + b * math.sin(a)) * rr)
                      for a in (2 * math.pi * k / seg for k in range(seg))])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    return p


def set_hidden(names, hidden=True):
    n = 0
    for nm in names:
        o = bpy.data.objects.get(nm)
        if not o:
            continue
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = hidden
        n += 1
    return n


def build():
    scene = bpy.context.scene
    lib = {}
    exec(open(bpy.path.abspath("//scripts/profile_furniture.py")).read(), lib)
    lib["materials"]()
    col = bpy.data.collections.get("Machines") or bpy.data.collections.new("Machines")
    fcol = bpy.data.collections.get("Furniture") or bpy.data.collections.new("Furniture")
    for c in (col, fcol):
        if c.name not in scene.collection.children:
            scene.collection.children.link(c)
        for o in list(c.objects):
            data = o.data
            bpy.data.objects.remove(o)
            if data is not None and data.users == 0:
                (bpy.data.curves if isinstance(data, bpy.types.Curve) else bpy.data.meshes).remove(data)
    materials()
    M.update(alusatin=mat("Mach_AluSatin", "#C3C7CB", 0.3, metal=1.0), mdf=mat("MDF", "#B48C5C", 0.8),
             mdfdark=mat("MDF_Mark", "#8E6C45", 0.8), felt=mat("FilterFelt", "#ECEAE4", 0.95),
             bag=mat("ChipBag", "#C9CED1", 0.25, coat=0.5), hose=mat("Hose_Flex", "#3B3F43", 0.55))

    # ---- placeholders out
    ph = ["Component_1046510", "Component_1046510.001", "PRSalpha 9660"]
    for o in bpy.data.objects["ROOT"].children:                       # shallow shelves along the SSW glass
        if o.name.startswith(("Component_1062473", "Component_1484326", "Component_1483885")):
            pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" for c in k.bound_box]
            if pts and min(p.x for p in pts) > 31.0:
                ph.append(o.name)
    hidden = set_hidden(ph)
    # (the colleague's ESE shelf units Component_289785* used to get their boards back here; the bank's back-wall
    #  shelving now stands there, so they stay hidden - see cleanup_leftovers.py)

    def unit_on(part_dims, cx, cy, facing):
        w, d = part_dims
        return lib["placement"](cx, cy, w, d, facing)

    def put(part, name, loc, rot, local_xy, z, w, d):
        """Machine centred at a local point of a furniture unit, same facing as the unit."""
        c = lib["to_world"](loc, rot, (local_xy[0], local_xy[1], 0))
        off = Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0))
        return part.emit(name, col, Vector((c.x, c.y, z)) + off, rot)

    # ---- laser room: machines, benches, storage and the central exhaust live in build_laser_room.py

    # ---- print farm: build_print_farm.py (run it after this script)
    k = 0

    # ---- CNC room: ShopBot PRSalpha 120-60 (HÍ's machine; Magnús 2026-11-26, ShopBot spec sheet: 3.66 x 2.31 m
    #      footprint, 3.28 x 1.55 m movement; the wiki still says 144-60, MPTVPC is correcting it). Geometry = the
    #      teaching wiki's own generator (MagnusPetursson/shopbot-prsalpha-wiki build.mjs) re-run with the 120-60
    #      table and travel, NOT scaled: rails, racks, side beams, trough and deck are shorter, legs/bearers/control
    #      box respaced, every part keeps its size (assets/wiki/README.md): 3.58 x 2.33 m table, 0.90 m deck, gantry parked, floor-standing dust boom, under-table
    #      control box + VFD, cable carriers and hoses at rest. Placement (mine): long axis along the room, boom end
    #      to the loading door, far end where it was, x-chain side to the glass aisle, far side 45 mm off the interior wall; front end at
    #      y 21.26 so the glass door's 1.0 m swing clears the x-chain (it touched the old machine too). Left out of
    #      the wiki set: its PC cart + pendant (the PC station is ours), its generic collector (the lab's ACword
    #      FT100 stands in the same spot; the floor hose is retargeted to its inlet), its demo stock/screws/clamps
    #      and the z-plate on the stock (build_jobs puts our job on the deck).
    _w = {}
    _HERE = bpy.path.abspath("//scripts/")
    exec(open(_HERE + "wiki_machine.py").read(), _w)
    sb_x0, sb_y0 = 24.09, 21.26 - 4.19                                  # wiki (0, 0) = far end, fixed at room y 17.07;
    #      the 120-60 table ends 0.61 m earlier than the 144-60 did (operator end at room y 20.65)
    METAL = {"alu": 1.0, "rail": 1.0, "gearbox": 0.9, "collet": 1.0, "carbide": 1.0, "zplate": 1.0, "prox": 0.8,
             "copper": 1.0, "clamp": 1.0, "shard": 1.0, "spindle": 0.0, "steel": 0.15}
    sb_done = {}
    # lab photo i-003, measured on the apron, leg and gantry end plate: one dark violet-navy paint (#151C45) for the
    # stand, side beams and the wiki's blue plates (gantry ends, carriage). Semi-gloss, no coat (a coat over dark paint read milky/powdery).
    NAVY = _w["srgb_mat"](bpy, "SB_frame_navy", "#151C45", 0.26)

    def sb_mat(name, e, mats):
        if name == "plate" or (e["name"].startswith(("side.", "stand."))
                               and not e["name"].startswith(("stand.nut", "stand.stem", "stand.pad"))):
            return NAVY
        if name == "mdf":
            return M["mdf"]
        if name == "ply":
            return lib["MAT"]["ply"]
        key = f"SB_{name}"
        if key in sb_done:
            return sb_done[key]
        c, sp = _w["srgb_to_lin"](mats[name]["rgb"]), mats[name]["spec"]   # wiki colours are sRGB display values
        m_ = bpy.data.materials.get(key) or bpy.data.materials.new(key)
        sb_done[key] = m_
        m_.use_nodes = True
        bs = next(n_ for n_ in m_.node_tree.nodes if n_.type == "BSDF_PRINCIPLED")
        bs.inputs["Base Color"].default_value = (*c, 1)
        bs.inputs["Metallic"].default_value = METAL.get(name, 0.0)
        bs.inputs["Roughness"].default_value = max(0.12, 0.72 - 0.6 * sp)
        if name in ("led", "label"):
            bs.inputs["Emission Color"].default_value = (*c, 1)
            bs.inputs["Emission Strength"].default_value = 0.6 if name == "led" else 0.0
        m_.diffuse_color = (*c, 1)
        return m_
    skip = re.compile(r"^(pc\.|pendant|tray|collector|stock|screw|clamp|cable\.(pendant|usb)|zplate$|zplate\.post$)")
    # hose.floor ends at the wiki collector's inlet (room 20.81, 16.45, 1.20): move it to the ACword inlet
    # (21.50, 16.72, 1.12). Local frame = room rotated -90 deg: local (dx, dy) = (room dy, -room dx).
    sbp, nparts, _d = _w["wiki_part"](Part, _HERE + "../assets/wiki/shopbot_prsalpha_120_60.json", sb_mat, skip=skip,
                                       retarget={"hose.floor": (0.27, -0.69, -0.08)})
    sbp.emit("ShopBot_PRSalpha_120_60", col, Vector((sb_x0, sb_y0, 0.0)), math.pi / 2)
    place(dust_collector(), "ACword_FT100", col, 21.50, 16.45, 0.0, 0.84, 0.50, "+y")
    print("ShopBot from the wiki:", nparts, "parts")
    return k, hidden


k, hidden = build()
print("printers", k, "| placeholders hidden", hidden)

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
