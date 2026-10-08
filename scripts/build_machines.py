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
    _rbox(p, M["white"], 0.0, w, 0.0, d, 0.012, h - 0.012, 0.03)                       # shell
    for x in (0.06, w - 0.06):                                                           # feet
        for y in (0.06, d - 0.06):
            p.cyl(M["rubber"], (x, y, 0.0), (x, y, 0.012), 0.022, seg=16)
    p.box(M["black"], 0.03, w - 0.03, -0.001, 0.0, 0.135, 0.137)                         # door seam (top)
    p.box(M["black"], 0.07, w - 0.07, -0.0015, 0.0, 0.082, 0.090)                        # pass-through slot
    p.box(M["smoke"], 0.10, w - 0.10, -0.002, -0.001, 0.0835, 0.0885)                    # Pro shield in the slot
    p.box(M["white"], 0.03, w - 0.03, 0.030, d - 0.105, h - 0.012, h - 0.004, bevel=0.004)  # lid frame
    p.box(M["smoke"], 0.055, w - 0.055, 0.050, d - 0.125, h - 0.0045, h - 0.0015)        # lid glass
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
    p.box(M["white"], 0.025, w - 0.025, 0.025, d - 0.080, h - 0.010, h - 0.004, bevel=0.003)
    p.box(M["amber"], 0.045, w - 0.045, 0.040, d - 0.095, h - 0.0045, h - 0.0015)         # orange lid
    _rbox(p, M["white"], 0.015, w - 0.015, d - 0.078, d - 0.010, h - 0.010, h + 0.003, 0.010)
    p.box(M["grey"], w * 0.35, w * 0.65, -0.002, 0.014, h - 0.026, h - 0.014, bevel=0.003)
    p.cyl(M["white"], (w - 0.055, 0.055, h - 0.005), (w - 0.055, 0.055, h + 0.002), 0.022, seg=28)
    p.cyl(glow, (w - 0.055, 0.055, h + 0.002), (w - 0.055, 0.055, h + 0.003), 0.016, seg=28)
    _port(p, w - 0.11, d, 0.060, 0.05)
    return p


def _acrylic(name, hexcol, rough=0.08, alpha=0.45):
    """Tinted acrylic sheet without refraction (alpha-blended colour + clear-coat reflections): thin sheets
    modelled as boxes otherwise render like warped chrome."""
    m = mat(name, hexcol, rough, coat=0.8)
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
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


def prusa(spool):
    """Prusa MK3S+ (~500 x 550 x 400): frame plate, rods, motors, PEI bed, orange parts, LCD, spool on top."""
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
    p.box(M["pei"], 0.125, w - 0.125, bed_y - 0.005, bed_y + 0.255, 0.060, 0.064, bevel=0.002)  # PEI sheet
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
    zx = 0.20
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
    # --- LCD box at the front left
    p.box(M["orange"], 0.10, 0.36, -0.035, 0.03, 0.01, 0.085, bevel=0.006)
    p.box(M["lcd"], 0.13, 0.27, -0.0365, -0.034, 0.03, 0.07)
    p.cyl(M["dark"], (0.31, -0.045, 0.05), (0.31, -0.035, 0.05), 0.011, seg=20)                  # knob
    # --- spool holder on the top bar + spool
    p.box(M["orange"], w / 2 - 0.012, w / 2 + 0.012, fy - 0.01, fy + 0.03, 0.40, 0.46, bevel=0.003)
    spool_part(p, spool, w / 2, fy + 0.045, 0.47)
    if PRINT_RNG.random() < 0.55:                                                               # a print in progress
        kind = PRINT_RNG.choice(("box", "vase", "bracket"))
        bx, by = w / 2 + PRINT_RNG.uniform(-0.06, 0.06), bed_y + 0.12 + PRINT_RNG.uniform(-0.04, 0.04)
        hgt = PRINT_RNG.uniform(0.015, 0.09)
        if kind == "vase":
            p.cyl(spool, (bx, by, 0.064), (bx, by, 0.064 + hgt), PRINT_RNG.uniform(0.025, 0.045), seg=40)
        elif kind == "box":
            sx, sy = PRINT_RNG.uniform(0.03, 0.09), PRINT_RNG.uniform(0.03, 0.09)
            p.box(spool, bx - sx / 2, bx + sx / 2, by - sy / 2, by + sy / 2, 0.064, 0.064 + hgt, bevel=0.002)
        else:
            p.box(spool, bx - 0.05, bx + 0.05, by - 0.015, by + 0.015, 0.064, 0.072, bevel=0.0015)
            p.box(spool, bx - 0.05, bx - 0.04, by - 0.015, by + 0.015, 0.072, 0.064 + hgt, bevel=0.0015)
    return p


def bambu(w=0.392, d=0.406, h=0.478):
    p = Part()
    p.box(M["dark"], 0, w, 0, d, 0, h, bevel=0.01)
    p.box(M["smoke"], 0.02, w - 0.02, -0.004, 0.01, 0.06, h - 0.03, bevel=0.004)               # glass door
    p.box(M["smoke"], 0.02, w - 0.02, 0.02, d - 0.02, h, h + 0.004)                             # glass top
    return p


def srm20(w=0.451, d=0.426, h=0.426):
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
    p.cyl(M["dark"], (w * 0.51, d - 0.17, 0.17), (w * 0.51, d - 0.17, 0.30), 0.022, seg=24) # spindle motor
    p.cyl(M["chrome"], (w * 0.51, d - 0.17, 0.13), (w * 0.51, d - 0.17, 0.17), 0.004, seg=8)  # end mill
    p.box(M["lcd"], w - 0.04, w - 0.02, -0.001, 0.0, 0.05, 0.07)                            # status LED
    return p


def vinyl(w=0.851, d=0.310, h=0.235):
    """Roland desktop vinyl cutter: grey body, black end caps, pinch-roller slot, vinyl roll behind."""
    p = Part()
    p.box(M["grey"], 0.07, w - 0.07, 0.05, d - 0.02, 0.03, h, bevel=0.025)
    for x0 in (0.0, w - 0.07):
        p.box(M["black"], x0, x0 + 0.07, 0.02, d, 0.0, h + 0.01, bevel=0.02)
    p.box(M["dark"], 0.07, w - 0.07, 0.035, 0.07, 0.10, 0.125, bevel=0.003)                   # media slot
    p.box(M["white"], 0.10, w - 0.10, 0.02, 0.05, 0.106, 0.110)                               # vinyl coming out
    p.box(M["black"], w - 0.16, w - 0.08, 0.16, 0.26, h - 0.002, h + 0.006, bevel=0.003)      # control panel
    p.box(M["lcd"], w - 0.15, w - 0.11, 0.18, 0.21, h + 0.006, h + 0.007)
    p.cyl(M["spools"][2], (0.12, d + 0.07, 0.07), (w - 0.12, d + 0.07, 0.07), 0.04, seg=32)   # roll on stand
    p.cyl(M["chrome"], (0.08, d + 0.07, 0.07), (w - 0.08, d + 0.07, 0.07), 0.008, seg=12)
    return p


def mayku(w=0.274, d=0.466, h=0.315):
    p = Part()
    p.box(M["white"], 0, w, 0.05, d - 0.05, 0, h, bevel=0.02)
    for y in (0.0, d - 0.05):
        p.box(M["dark"], 0.06, w - 0.06, y, y + 0.05, h * 0.6, h * 0.7, bevel=0.008)           # handles
    return p


def sewing(w=0.42, d=0.20, h=0.30):
    """Domestic sewing machine: bed, pillar, arm, needle head, hand wheel, thread spool, screen."""
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, 0.085, bevel=0.018)                                  # bed
    p.box(M["white"], w - 0.12, w - 0.01, 0.015, d - 0.015, 0.06, h, bevel=0.025)          # pillar
    p.box(M["white"], 0.02, w - 0.01, 0.025, d - 0.025, h - 0.085, h, bevel=0.025)         # arm
    p.box(M["white"], 0.02, 0.10, 0.03, d - 0.03, 0.12, h - 0.06, bevel=0.012)            # needle head
    p.cyl(M["chrome"], (0.06, 0.07, 0.09), (0.06, 0.07, 0.125), 0.003, seg=8)            # needle
    p.box(M["chrome"], 0.045, 0.085, 0.05, 0.09, 0.085, 0.09)                             # presser foot
    p.cyl(M["white"], (w - 0.005, d / 2, h - 0.06), (w + 0.025, d / 2, h - 0.06), 0.045, seg=32)  # hand wheel
    p.cyl(M["chrome"], (w - 0.06, d / 2, h), (w - 0.06, d / 2, h + 0.05), 0.003, seg=8)  # spool pin
    p.cyl(M["spools"][0], (w - 0.06, d / 2, h + 0.005), (w - 0.06, d / 2, h + 0.045), 0.016, seg=20)
    p.box(M["lcd"], w - 0.10, w - 0.04, -0.001, 0.0, 0.15, 0.22)
    p.box(M["dark"], 0.11, w - 0.13, -0.001, 0.0, h - 0.07, h - 0.04)                     # front decal strip
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


def overlock(w=0.33, d=0.28, h=0.29):
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, h * 0.7, bevel=0.03)
    for i, x in enumerate((0.08, 0.13, 0.18, 0.23)):                                            # thread cones
        p.cyl(M["spools"][i], (x, d * 0.6, h * 0.7), (x, d * 0.6, h * 1.25), 0.018, seg=12)
    return p


def shopbot(W=2.15, Lg=4.30):
    """ShopBot PRS Alpha 120 (60" x 120" table): black steel frame, MDF spoilboard, aluminium gantry."""
    p = Part()
    blk, alu, mdf = M["black"], M["alusatin"], M["mdf"]
    for x in (0.08, W - 0.20):                                                                  # side beams
        p.box(blk, x, x + 0.12, 0.0, Lg, 0.62, 0.82, bevel=0.004)
        p.box(alu, x + 0.02, x + 0.10, 0.0, Lg, 0.82, 0.85)                                    # Y rails
    for y in (0.15, 1.45, 2.85, Lg - 0.23):                                                    # legs + feet + cross members
        for x in (0.10, W - 0.18):
            p.box(blk, x, x + 0.08, y, y + 0.08, 0.04, 0.62)
            p.cyl(M["rubber"], (x + 0.04, y + 0.04, 0.0), (x + 0.04, y + 0.04, 0.04), 0.045, seg=16)
        p.box(blk, 0.10, W - 0.10, y, y + 0.06, 0.25, 0.31)
        p.box(blk, 0.10, W - 0.10, y, y + 0.06, 0.70, 0.78)
    p.box(mdf, 0.22, W - 0.22, 0.10, Lg - 0.10, 0.80, 0.86)                                   # spoilboard
    for i in range(12):                                                                         # surfacing marks
        y = 0.25 + i * 0.32
        p.box(M["mdfdark"], 0.24, W - 0.24, y, y + 0.004, 0.8601, 0.8605)
    gy = Lg * 0.42                                                                              # gantry position
    for x in (0.02, W - 0.12):                                                                  # gantry side cars
        p.box(blk, x, x + 0.10, gy - 0.20, gy + 0.20, 0.78, 1.32, bevel=0.006)
    p.box(alu, 0.0, W, gy - 0.07, gy + 0.07, 1.20, 1.40, bevel=0.006)                          # gantry beam
    p.box(blk, 0.0, W, gy + 0.07, gy + 0.09, 1.30, 1.40)                                       # cable tray on beam
    cx = W * 0.45
    p.box(blk, cx - 0.14, cx + 0.14, gy - 0.16, gy - 0.07, 1.10, 1.45, bevel=0.005)            # X car
    p.box(blk, cx - 0.08, cx + 0.08, gy - 0.26, gy - 0.16, 0.98, 1.52, bevel=0.005)            # Z axis
    p.cyl(alu, (cx, gy - 0.21, 0.95), (cx, gy - 0.21, 1.18), 0.045, seg=24)                    # spindle
    p.cyl(blk, (cx, gy - 0.21, 0.90), (cx, gy - 0.21, 0.95), 0.10, seg=24)                     # dust shoe
    p.box(blk, W - 0.06, W, 0.2, Lg - 0.2, 0.86, 0.96)                                          # cable chain
    return p


def dust_collector(w=0.84, d=0.50, h=2.20):
    """ACword FT100 single-bag collector: stand, motor/impeller, white filter bag, clear lower bag."""
    p = Part()
    cx = w / 2
    for x in (0.08, w - 0.12):
        for y in (0.08, d - 0.12):
            p.box(M["dark"], x, x + 0.04, y, y + 0.04, 0.0, 1.0)
    p.cyl(M["dark"], (cx, d / 2, 0.98), (cx, d / 2, 1.06), 0.27, seg=32)                       # ring
    p.cyl(M["grey"], (cx - 0.05, d / 2, 1.12), (cx + 0.30, d / 2, 1.12), 0.17, seg=28)         # motor
    p.cyl(M["grey"], (cx, -0.02, 1.12), (cx, d / 2, 1.12), 0.06, seg=20)                       # inlet
    p.cyl(M["felt"], (cx, d / 2, 1.06), (cx, d / 2, h - 0.06), 0.24, seg=32)                   # filter bag
    bmesh.ops.create_uvsphere(p.bm(M["felt"]), u_segments=32, v_segments=8, radius=0.24,
                              matrix=Matrix.Translation((cx, d / 2, h - 0.06)) @ Matrix.Scale(0.25, 4, (0, 0, 1)))
    p.cyl(M["bag"], (cx, d / 2, 0.10), (cx, d / 2, 0.98), 0.24, seg=32)                       # chip bag
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


def einscan_se():
    """Shining 3D EinScan SE V2 (570 x 210 x 210 assembled; checked against Shining 3D photos): black turntable on a
    flat black arm, angled black stand at the far end carrying the dark-grey scanner head (projector between two
    cameras) aimed at the turntable; a printed figure on the turntable."""
    p = Part()
    blk = mat("Scanner_Black", "#16171A", 0.35)
    head = mat("Scanner_Grey", "#3E4246", 0.35, metal=0.3)
    tc = Vector((0.105, 0.105, 0.0))
    p.cyl(blk, tc, tc + Vector((0, 0, 0.055)), 0.100, seg=40)                      # turntable base
    p.cyl(M["dark"], tc + Vector((0, 0, 0.055)), tc + Vector((0, 0, 0.060)), 0.090, seg=40)   # rotating disc
    p.box(blk, 0.10, 0.50, 0.075, 0.135, 0.0, 0.018, bevel=0.004)                  # flat arm
    _obox(p, blk, Vector((0.505, 0.105, 0.135)), (0.035, 0.055, 0.27), Matrix.Rotation(-0.22, 3, "Y"))  # stand
    rot = Matrix.Rotation(0.42, 3, "Y")                                            # head tilted down to the table
    hc = Vector((0.49, 0.105, 0.285))
    _obox(p, head, hc, (0.075, 0.250, 0.065), rot)
    face = hc + rot @ Vector((-0.0385, 0.0, 0.0))
    for dy, r in ((-0.085, 0.011), (0.0, 0.016), (0.085, 0.011)):                 # cameras + projector lens
        c = face + Vector((0, dy, 0))
        p.cyl(M["black"], c, c + rot @ Vector((-0.006, 0, 0)), r, seg=20)
        p.cyl(M["lcd"] if dy == 0 else M["smoke"], c + rot @ Vector((-0.006, 0, 0)), c + rot @ Vector((-0.007, 0, 0)), r * 0.7, seg=20)
    fig = M["spools"][3]                                                            # orange printed figure
    p.cyl(fig, tc + Vector((0, 0, 0.060)), tc + Vector((0, 0, 0.075)), 0.035, seg=24)
    p.cyl(fig, tc + Vector((0, 0, 0.075)), tc + Vector((0, 0, 0.150)), 0.018, seg=20)
    bmesh.ops.create_uvsphere(p.bm(fig), u_segments=20, v_segments=10, radius=0.028,
                              matrix=Matrix.Translation(tc + Vector((0, 0, 0.170))))
    return p


def secabo_tc7(w=0.43, d=0.57, open_deg=24):
    """Secabo TC7 40 x 50 cm clam heat press (43 x 57 x 75 closed; checked against Secabo photos), shown open:
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

    # ---- CNC room: ShopBot PRS Alpha 120 against the interior wall (x 24.15), collector out by the far glass
    #      corner, control box on the glass side (user layout, 2026-10-07)
    W, Lg = 2.15, 4.30
    sb_loc = Vector((24.13 - W, 22.75 - Lg, 0.0))
    shopbot(W, Lg).emit("ShopBot_PRSAlpha_120", col, sb_loc, 0.0)
    place(dust_collector(), "ACword_FT100", col, 21.50, 16.45, 0.0, 0.84, 0.50, "+y")
    place(control_box(), "ShopBot_Control", col, 21.17, 21.95, 0.0, 0.50, 0.30, "+x")
    # dust extraction: brush skirt on the spindle, ribbed hose up to a ceiling-hung swing boom (40x40 profile on
    # a drop rod by the collector), along the boom in rings, spring balancer at the boom end, down to the inlet
    gy = sb_loc.y + Lg * 0.42
    hx = sb_loc.x + W * 0.45
    sx, sy = hx, gy - 0.21                                              # spindle axis
    dx = Part()
    dx.cyl(mat("Brush_Black", "#141414", 0.95), (sx, sy, 0.845), (sx, sy, 0.905), 0.108, seg=32)   # brush skirt
    dx.cyl(M["hose"], (sx + 0.07, sy, 0.95), (sx + 0.11, sy, 1.10), 0.045, seg=20)                 # shoe port
    pv, end = Vector((21.65, 17.55, 2.90)), Vector((sx, sy - 0.10, 2.90))
    axis = end - pv
    dx.cyl(M["galv"], (pv.x, pv.y, 3.93), (pv.x, pv.y, pv.z + 0.06), 0.03, seg=16)                 # drop rod
    dx.cyl(M["galv"], (pv.x, pv.y, pv.z + 0.02), (pv.x, pv.y, pv.z + 0.08), 0.07, seg=24)           # swivel bearing
    q = axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.create_cube(dx.bm(lib["MAT"]["profile"]), size=1.0,
                          matrix=Matrix.Translation(pv + axis / 2) @ q @ Matrix.Diagonal((0.04, 0.04, axis.length, 1)))
    dx.cyl(M["galv"], (pv.x, pv.y, 3.55), tuple(pv + axis * 0.6 + Vector((0, 0, 0.02))), 0.004, seg=8)  # tie rod
    for t in (0.2, 0.42, 0.64, 0.86):                                                                 # hose rings
        c = pv + axis * t - Vector((0, 0, 0.12))
        dx.cyl(M["galv"], tuple(c + Vector((0, 0, 0.10))), tuple(c + Vector((0, 0, 0.065))), 0.004, seg=6)
        bmesh.ops.create_cone(dx.bm(M["galv"]), cap_ends=False, segments=24, radius1=0.066, radius2=0.066, depth=0.012,
                              matrix=Matrix.Translation(c) @ q)
    dx.box(M["dark"], end.x - 0.04, end.x + 0.04, end.y - 0.03, end.y + 0.03, 2.72, 2.88, bevel=0.006)  # balancer
    dx.cyl(M["galv"], (end.x, end.y, 2.72), (end.x, end.y, 2.30), 0.0015, seg=6)
    dx.emit("ShopBot_DustBoom", col, Vector((0, 0, 0)), 0.0)
    path = [Vector(v) for v in ((sx + 0.11, sy, 1.10), (sx + 0.14, sy - 0.02, 1.45), (end.x + 0.06, end.y + 0.02, 2.05),
                                (end.x, end.y, 2.26))]
    path += [pv + axis * t - Vector((0, 0, 0.12)) for t in (0.86, 0.64, 0.42, 0.2)]
    path += [Vector(v) for v in ((21.60, 17.40, 2.55), (21.52, 17.15, 1.90), (21.50, 17.00, 1.35), (21.50, 16.86, 1.14),
                                 (21.50, 16.72, 1.12))]
    ribbed_hose(M["hose"], path, 0.055).emit("ShopBot_DustHose", col, Vector((0, 0, 0)), 0.0)
    return k, hidden


k, hidden = build()
print("printers", k, "| placeholders hidden", hidden)
