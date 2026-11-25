"""Profile cupboard on the mural wall where the colleague's kitchen sink was. Re-runnable.

The mural wall (faces +y at y 21.84) has 1.5 m free between the CNC-room corner (x 24.26) and the
red door portal (x ~25.75). The SketchUp sink (collection "Кухня": basin + tap) and its drainer
ribs ("мебели" Component_939793*) are hidden; in their place a low black 40x40 profile cupboard
with a birch top at counter height (the double socket at 1.10 m stays usable above it):
left bay = hinged birch door with an inner shelf, right bay = three graded birch drawers.
"""
import bpy
from mathutils import Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
Part, mat = lib["Part"], lib["simple_mat"]

X0, WALL = 24.32, 21.85                # left end (CNC corner side), back against the mural wall
BAYS, D, H = [0.63, 0.63], 0.45, 0.88  # frame height; birch top 25 mm on it -> 0.905 m
SINK = ("Кухня",)
DRAINER = "Component_939793"


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("MuralCupboard") or bpy.data.collections.new("MuralCupboard")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    # sink, tap and drainer out
    gone = [o for c in SINK if c in bpy.data.collections for o in bpy.data.collections[c].all_objects]
    gone += [o for o in bpy.data.objects if o.name.startswith(DRAINER)]
    for o in gone:
        o.hide_render = o.hide_viewport = True

    part, slots, L = lib["shelf_unit"](BAYS, D, H, [0.12], power=False)
    loc, rot = lib["placement"](X0 + L / 2, WALL + D / 2, L, D, "+y")
    blk = mat("Handle_Black", "#151515", 0.4)
    gap = mat("Drawer_Shadow", "#0E0E0E", 0.9)
    label = mat("Drawer_Label", "#F3F1EA", 0.6)
    z0, z1 = 0.10, H - 0.045                                           # between bottom and top frame rails
    for x in (0.012, L - 0.028):                                       # birch side panels set in the end posts
        part.box(MAT["ply"], x, x + 0.016, 0.04, D - 0.04, z0, z1, bevel=0.001)
    # left bay: carcass, inner shelf, hinged door with a vertical bar pull on the drawer side
    xa, xb, _, _, _ = slots[(0, 0)]
    part.box(gap, xa, xb, 0.020, D - 0.01, z0, z1)
    part.box(MAT["ply"], xa + 0.002, xb - 0.002, 0.022, D - 0.012, 0.47, 0.488, bevel=0.001)
    part.box(MAT["ply"], xa + 0.003, xb - 0.003, -0.002, 0.016, z0 + 0.003, z1 - 0.003, bevel=0.0015)
    part.box(blk, xb - 0.05, xb - 0.035, -0.020, -0.002, z1 - 0.26, z1 - 0.06, bevel=0.002)
    # right bay: three graded drawers (as the component storage)
    xa, xb, _, _, _ = slots[(1, 0)]
    heights = [0.40, 0.33, 0.27]
    z = z0
    for hgt in heights:
        hh = (z1 - z0) * hgt / sum(heights)
        part.box(gap, xa, xb, 0.010, D - 0.01, z, z + hh)
        part.box(MAT["ply"], xa + 0.003, xb - 0.003, -0.002, 0.016, z + 0.003, z + hh - 0.003, bevel=0.0015)
        part.box(blk, (xa + xb) / 2 - 0.08, (xa + xb) / 2 + 0.08, -0.020, -0.002, z + hh - 0.05, z + hh - 0.035, bevel=0.002)
        part.box(label, xa + 0.04, xa + 0.14, -0.0025, -0.002, z + hh - 0.06, z + hh - 0.035)
        z += hh
    part.box(MAT["ply"], -0.005, L + 0.005, -0.01, D, H, H + 0.025, bevel=0.002)   # solid birch top
    part.emit("MuralCupboard", col, loc, rot)
    print("cupboard x %.2f-%.2f, y %.2f-%.2f, top %.3f m; hid %d sink objects" % (X0, X0 + L, WALL, WALL + D, H + 0.025, len(gone)))


build()

# Placements come from layout/layout.yaml (layout/README.md): built at this builder's coordinates, then moved there.
_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]()
