"""Machines from refs/equipment (the list supplied to the architects), as simplified
but recognisable models at the listed sizes. Re-runnable: rebuilds the "Machines"
collection. Run inside Blender: exec(open(path).read()).

Placement (model frame: +X = SSW, +Y = ESE):
  Laser room (glazed room x 29.67-32.53, y 20.14-26.92): Epilog Fusion Edge 24 against
  the NNE partition; 2x Glowforge Pro HD, Glowforge Aura, xTool F1 Ultra on black
  electric desks along the SSW glass; 100/80 mm exhausts straight out through the
  facade edge beam (Epilog run > 2.5 m gets an inline fan, per the spec).
  Print farm: 12x Prusa MK3S+ on the ESE shelving (two boards per unit hidden -> 0.8 m pitch).
  Benches: Bambu Lab P2S, Roland SRM-20, Roland vinyl cutter, Mayku, sewing machine.
  The CNC (colleague's ShopBot 96x60) is left as is pending confirmation of the PRS Alpha 120.
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
        pei=mat("Mach_PEI", "#2B2622", 0.6),
        lcd=mat("Mach_LCD", "#3D7BD9", 0.2, emit=1.5),
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
            bm.free()
            for p in me.polygons:
                p.use_smooth = True
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


def glowforge(w, d, h, lid):
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, h - 0.004, bevel=0.025)
    b = 0.045
    p.box(lid, b, w - b, b, d - b, h - 0.012, h, bevel=0.006)                                   # tinted lid
    p.box(M["white"], w * 0.3, w * 0.7, -0.012, 0.0, h * 0.55, h * 0.75, bevel=0.004)          # front handle lip
    return p


def epilog(w=1.055, d=0.834, h=0.967):
    p = Part()
    base = 0.60
    p.box(M["black"], 0.02, w - 0.02, 0.02, d - 0.02, 0.09, base, bevel=0.01)                    # cabinet
    for x in (0.08, w - 0.08):                                                                    # casters
        for y in (0.08, d - 0.08):
            p.cyl(M["rubber"], (x - 0.02, y, 0.04), (x + 0.02, y, 0.04), 0.04)
    p.box(M["grey"], 0, w, 0, d, base, h - 0.06, bevel=0.015)                                    # body
    # sloped smoked lid over the front 2/3
    p.box(M["smoke"], 0.03, w - 0.03, 0.02, d * 0.66, h - 0.06, h - 0.035, bevel=0.01)
    p.box(M["grey"], 0.0, w, d * 0.66, d, h - 0.06, h, bevel=0.012)                              # rear housing
    p.box(M["red"], 0.0, w, -0.002, 0.004, base + 0.08, base + 0.11)                             # red stripe
    p.box(M["dark"], w - 0.20, w - 0.05, d * 0.70, d * 0.92, h, h + 0.012, bevel=0.004)         # control panel
    p.box(M["lcd"], w - 0.18, w - 0.08, d * 0.73, d * 0.80, h + 0.012, h + 0.014)
    return p


def xtool(w=0.493, d=0.253, h=0.373):
    p = Part()
    p.box(M["dark"], 0, w, 0, d, 0, h, bevel=0.012)
    p.box(M["amber"], 0.03, w - 0.03, -0.004, 0.02, 0.08, h - 0.05, bevel=0.006)               # shield window
    return p


def prusa(spool):
    """Prusa MK3S+ (500 x 550 x 400): black frame, orange parts, PEI bed, spool on top."""
    p = Part()
    w, d = 0.50, 0.55
    for x in (0.13, w - 0.13):                                                                   # Y rails
        p.box(M["alu"], x - 0.01, x + 0.01, 0.04, d - 0.04, 0.0, 0.04)
    p.box(M["orange"], 0.10, w - 0.10, 0.03, 0.05, 0.0, 0.07, bevel=0.004)                      # front/back plates
    p.box(M["orange"], 0.10, w - 0.10, d - 0.05, d - 0.03, 0.0, 0.07, bevel=0.004)
    p.box(M["pei"], 0.125, 0.375, 0.17, 0.38, 0.075, 0.08, bevel=0.002)                         # bed
    p.box(M["alu"], 0.11, 0.39, 0.16, 0.39, 0.065, 0.075)
    fy = 0.30                                                                                     # main frame plane
    p.box(M["alu"], 0.03, 0.06, fy - 0.015, fy + 0.015, 0.0, 0.38)
    p.box(M["alu"], w - 0.06, w - 0.03, fy - 0.015, fy + 0.015, 0.0, 0.38)
    p.box(M["alu"], 0.03, w - 0.03, fy - 0.015, fy + 0.015, 0.36, 0.40)
    p.box(M["alu"], 0.03, w - 0.03, fy - 0.015, fy + 0.015, 0.0, 0.05)
    for zz in (0.215, 0.26):                                                                     # X rods
        p.cyl(M["chrome"], (0.07, fy - 0.03, zz), (w - 0.07, fy - 0.03, zz), 0.004, seg=8)
    p.box(M["orange"], 0.05, 0.10, fy - 0.06, fy + 0.0, 0.18, 0.30, bevel=0.004)                # X ends
    p.box(M["orange"], w - 0.10, w - 0.05, fy - 0.06, fy + 0.0, 0.18, 0.30, bevel=0.004)
    p.box(M["orange"], 0.21, 0.29, fy - 0.10, fy - 0.03, 0.17, 0.30, bevel=0.005)               # extruder
    p.box(M["black"], 0.225, 0.275, fy - 0.12, fy - 0.10, 0.20, 0.28, bevel=0.003)              # fan
    p.box(M["orange"], 0.14, 0.36, -0.01, 0.03, 0.02, 0.09, bevel=0.005)                        # LCD box
    p.box(M["lcd"], 0.17, 0.30, -0.012, -0.009, 0.035, 0.075)
    p.cyl(spool, (w / 2 - 0.035, fy + 0.04, 0.47), (w / 2 + 0.035, fy + 0.04, 0.47), 0.085, seg=24)  # spool
    p.box(M["alu"], w / 2 - 0.01, w / 2 + 0.01, fy - 0.01, fy + 0.01, 0.40, 0.44)
    return p


def bambu(w=0.392, d=0.406, h=0.478):
    p = Part()
    p.box(M["dark"], 0, w, 0, d, 0, h, bevel=0.01)
    p.box(M["smoke"], 0.02, w - 0.02, -0.004, 0.01, 0.06, h - 0.03, bevel=0.004)               # glass door
    p.box(M["smoke"], 0.02, w - 0.02, 0.02, d - 0.02, h, h + 0.004)                             # glass top
    return p


def srm20(w=0.451, d=0.426, h=0.426):
    p = Part()
    p.box(M["white"], 0, w, 0.05, d, 0, h, bevel=0.015)
    p.box(M["purple"], 0.02, w - 0.02, 0.0, 0.32, 0.06, h - 0.02, bevel=0.01)                  # tinted cover
    return p


def vinyl(w=0.851, d=0.310, h=0.235):
    p = Part()
    p.box(M["grey"], 0, w, 0.04, d, 0, h, bevel=0.03)
    p.box(M["dark"], 0.05, w - 0.05, 0.0, 0.06, 0.09, 0.13, bevel=0.005)                       # feed slot lip
    p.box(M["dark"], w - 0.16, w - 0.03, 0.08, 0.20, h, h + 0.008, bevel=0.003)                # panel
    return p


def mayku(w=0.274, d=0.466, h=0.315):
    p = Part()
    p.box(M["white"], 0, w, 0.05, d - 0.05, 0, h, bevel=0.02)
    for y in (0.0, d - 0.05):
        p.box(M["dark"], 0.06, w - 0.06, y, y + 0.05, h * 0.6, h * 0.7, bevel=0.008)           # handles
    return p


def sewing(w=0.42, d=0.20, h=0.30):
    p = Part()
    p.box(M["white"], 0, w, 0, d, 0, 0.09, bevel=0.015)                                        # bed
    p.box(M["white"], w - 0.11, w - 0.01, 0.02, d - 0.02, 0.09, h, bevel=0.02)                 # pillar
    p.box(M["white"], 0.03, w - 0.01, 0.02, d - 0.02, h - 0.09, h, bevel=0.02)                 # arm
    p.box(M["dark"], 0.05, 0.13, 0.03, d - 0.03, 0.10, h - 0.09)                                # needle head
    p.box(M["lcd"], w - 0.10, w - 0.04, -0.002, 0.0, 0.15, 0.22)
    return p


# ---------------------------------------------------------------- placement helpers
def top_of(name):
    o = bpy.data.objects[name]
    pts = [k.matrix_world @ Vector(c) for k in (o, *o.children_recursive) if k.type == "MESH" and not k.hide_render for c in k.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts), max(p.z for p in pts))


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


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Machines") or bpy.data.collections.new("Machines")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        me = o.data
        bpy.data.objects.remove(o)
        if me and me.users == 0:
            bpy.data.meshes.remove(me)
    materials()

    # ---- laser room: desks along the SSW glass, fronts facing -x (into the room)
    GX0, GX1 = 31.85, 32.45
    xc = (GX0 + GX1) / 2
    place(desk(2.5), "Desk_250", col, xc, 20.30 + 1.25, 0, 2.5, 0.6, "-x")
    place(desk(2.0), "Desk_200", col, xc, 22.85 + 1.0, 0, 2.0, 0.6, "-x")
    H = 0.75
    for i, y in enumerate((20.85, 22.00)):
        place(glowforge(0.965, 0.527, 0.211, M["smoke"]), f"Glowforge_ProHD_{i + 1}", col, GX1 - 0.03 - 0.527 / 2, y, H, 0.965, 0.527, "-x")
    place(glowforge(0.556, 0.521, 0.127, M["grey"]), "Glowforge_Aura", col, GX1 - 0.03 - 0.521 / 2, 23.25, H, 0.556, 0.521, "-x")
    place(xtool(), "xTool_F1_Ultra", col, GX1 - 0.05 - 0.253 / 2, 24.05, H, 0.493, 0.253, "-x")
    place(epilog(), "Epilog_FusionEdge24", col, 29.70 + 0.834 / 2, 20.30 + 1.055 / 2 + 0.05, 0, 1.055, 0.834, "+x")
    # exhausts: up behind each machine, then straight out through the edge beam (z 3.75)
    ZE, XOUT = 3.75, 32.85
    for name, y, z0, r in (("Glowforge_ProHD_1", 20.85, H + 0.10, 0.05), ("Glowforge_ProHD_2", 22.00, H + 0.10, 0.05),
                           ("Glowforge_Aura", 23.25, H + 0.08, 0.05), ("xTool_F1_Ultra", 24.05, H + 0.25, 0.04)):
        exhaust(col, f"Exhaust_{name}", [(GX1 - 0.04, y, z0), (GX1 - 0.04, y, ZE), (XOUT, y, ZE)], r)
    ye = 20.30 + 1.055 / 2 + 0.05
    exhaust(col, "Exhaust_Epilog", [(29.75, ye, 0.85), (29.75, ye, ZE), (XOUT, ye, ZE)], 0.05)
    fan = Part()                                                       # inline fan on the long Epilog run
    fan.cyl(M["galv"], (30.9, ye, ZE), (31.25, ye, ZE), 0.13, seg=28)
    fan.emit("Exhaust_Epilog_InlineFan", col, Vector((0, 0, 0)), 0.0)
    hoods = Part()                                                     # wall caps outside
    for y in (20.85, 22.00, 23.25, 24.05, ye):
        hoods.box(M["galv"], XOUT, XOUT + 0.06, y - 0.09, y + 0.09, ZE - 0.09, ZE + 0.09, bevel=0.01)
    hoods.emit("Exhaust_Hoods", col, Vector((0, 0, 0)), 0.0)

    # ---- print farm on the ESE shelving: hide two boards per unit -> two 0.8 m levels
    farm = ["Component_289785", "Component_289785.001", "Component_289785.002"]
    k = 0
    for unit in farm:
        u = bpy.data.objects[unit]
        for c in u.children_recursive:
            if c.type == "MESH" and c.parent and c.parent.name.startswith("Plywood"):
                zt = max((c.matrix_world @ Vector(v)).z for v in c.bound_box)
                if abs(zt - 1.035) < 0.02 or abs(zt - 1.841) < 0.02:
                    c.hide_render = c.hide_viewport = True
        x0, x1, y0, y1, _ = top_of(unit)
        for level in (0.643, 1.441):
            for fx in (0.25, 0.75):
                spool = M["spools"][k % len(M["spools"])]
                place(prusa(spool), f"Prusa_MK3S_{k + 1:02d}", col, x0 + (x1 - x0) * fx, (y0 + y1) / 2, level, 0.50, 0.55, "-y")
                k += 1

    # ---- benchtop machines
    def on_bench(bench, part, name, w, d, facing, fx=0.5, fy=0.5):
        x0, x1, y0, y1, zt = top_of(bench)
        return place(part, name, col, x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy, zt, w, d, facing)
    on_bench("Component_237631.006", bambu(), "Bambu_P2S", 0.392, 0.406, "-y", fx=0.3)
    on_bench("Component_237631", srm20(), "Roland_SRM20", 0.451, 0.426, "+x", fy=0.3)
    on_bench("Component_237631.002", vinyl(), "Roland_VinylCutter", 0.851, 0.310, "-x")
    on_bench("Component_237631.004", mayku(), "Mayku_FormBox", 0.274, 0.466, "-x", fy=0.35)
    on_bench("Component_237631.003", sewing(), "Brother_Sewing", 0.42, 0.20, "+x", fy=0.6)
    return k


n = build()
print("machines built;", n, "printers")
