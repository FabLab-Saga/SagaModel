"""Entrance from the hotel's main hall (the SSW door at y 35.11-36.21 opens onto Bændahöllin's hall, not the
street). Fab Lab signage on the hall side. Re-runnable (collection "HallEntrance").

- Fascia sign above the door + fire-glass panel (hall face of the corner-bay wall x 34.44, z ~2.45-2.88; door moved
  to the bay per the city drawings, build_entrance_bay.py): black panel, the Fab Lab icon
  (refs/branding/logos/fablab_icon.svg) + "FAB" bold / "LAB SAGA" light (Roboto Condensed, like the mural logo).
- Plaque right of the door (hall side): name, partners, opening hours.
- Door decal: white vinyl icon + FAB LAB SAGA on the door glass.
Also renames the camera Cam_ExteriorEntrance -> Cam_HallEntrance.
"""
import math

import bpy
from mathutils import Matrix, Vector

ROOT = bpy.path.abspath("//")
WALL_X = 34.44                     # hall-side face of the corner-bay wall around the door
GLASS_X = 34.3405                  # hall-side face of the fixed fire-glass panel
FONTS = ROOT + "refs/branding/fonts/"


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def mat(name, hexcol, rough=0.4, emit=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = lin(hexcol)
        b.inputs["Emission Strength"].default_value = emit
    m.diffuse_color = lin(hexcol)
    return m


def font(fname):
    return next((f for f in bpy.data.fonts if bpy.path.abspath(f.filepath) == FONTS + fname), None) or bpy.data.fonts.load(FONTS + fname)


def facing_plus_x(ob, x, y, z):
    """Text/curve drawn in local XY -> on a wall facing +x, reading along +y."""
    s = ob.scale.copy()
    ob.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.pi / 2, 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X") \
        @ Matrix.Diagonal((*s, 1))


def text(col, name, body, fname, size, m, extrude=0.0015):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body, cu.size, cu.extrude = body, size, extrude
    cu.font = font(fname)
    cu.materials.append(m)
    ob = bpy.data.objects.new(name, cu)
    col.objects.link(ob)
    return ob


def icon(col, name, m, height):
    """Import the Fab Lab icon SVG once; returns a mesh object (local XY, centred, `height` tall)."""
    me = bpy.data.meshes.get("FabLab_Icon_Mesh")
    if me is None:
        before = set(bpy.data.objects)
        bpy.ops.import_curve.svg(filepath=ROOT + "refs/branding/logos/fablab_icon.svg")
        new = [o for o in bpy.data.objects if o not in before]
        dg = bpy.context.evaluated_depsgraph_get()
        import bmesh
        bm = bmesh.new()
        for o in new:
            if o.type == "CURVE":
                o.data.dimensions, o.data.fill_mode = "2D", "BOTH"
                tmp = o.evaluated_get(dg).to_mesh()
                tmp.transform(o.matrix_world)
                bm.from_mesh(tmp)
                o.evaluated_get(dg).to_mesh_clear()
        cols = {c for o in new for c in o.users_collection}
        for o in new:
            bpy.data.objects.remove(o)
        for c in cols:
            if c.name != "Scene Collection" and not c.objects and c.name.endswith(".svg"):
                bpy.data.collections.remove(c)
        xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]
        cx, cy, h = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, max(ys) - min(ys)
        bmesh.ops.transform(bm, matrix=Matrix.Diagonal((1 / h, 1 / h, 1, 1)) @ Matrix.Translation((-cx, -cy, 0)), verts=bm.verts)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        me = bpy.data.meshes.new("FabLab_Icon_Mesh")
        bm.to_mesh(me)
        bm.free()
    ob = bpy.data.objects.new(name, me)
    ob.data.materials.clear()
    ob.data.materials.append(m)
    ob.scale = (height, height, height)
    col.objects.link(ob)
    return ob


def width(ob):
    bpy.context.view_layer.update()
    return ob.dimensions.x


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("HallEntrance") or bpy.data.collections.new("HallEntrance")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        bpy.data.objects.remove(o)
    black, white = mat("Sign_Black", "#141414", 0.35), mat("Sign_White", "#F4F4F2", 0.45)
    vinyl = mat("Vinyl_White", "#F2F2F0", 0.5)
    # ---- fascia sign above the door: [icon] FAB LAB SAGA, centred over fire glass + door
    yc, zc, H = 36.255, 2.665, 0.40
    ic = icon(col, "Hall_Sign_Icon", white, 0.30)
    t1 = text(col, "Hall_Sign_FAB", "FAB", "RobotoCondensed-Bold.ttf", 0.28, white)
    t2 = text(col, "Hall_Sign_LABSAGA", "LAB SAGA", "RobotoCondensed-Light.ttf", 0.28, white)
    w_ic, w1, w2, gap = 0.30, width(t1), width(t2), 0.07
    total = w_ic + gap + w1 + gap * 0.8 + w2
    y = yc - total / 2
    facing_plus_x(ic, WALL_X + 0.024, y + w_ic / 2, zc)
    y += w_ic + gap
    facing_plus_x(t1, WALL_X + 0.022, y, zc - 0.10)
    y += w1 + gap * 0.8
    facing_plus_x(t2, WALL_X + 0.022, y, zc - 0.10)
    pw = total + 0.30
    panel = bpy.data.meshes.new("Hall_Sign_Panel")
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((WALL_X + 0.01, yc, zc)) @ Matrix.Diagonal((0.02, pw, H, 1)))
    bm.to_mesh(panel); bm.free()
    panel.materials.append(black)
    col.objects.link(bpy.data.objects.new("Hall_Sign_Panel", panel))
    # ---- plaque right of the door
    py, pz = 38.20, 1.52
    pl = bpy.data.meshes.new("Hall_Plaque")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((WALL_X + 0.006, py, pz)) @ Matrix.Diagonal((0.012, 0.46, 0.34, 1)))
    bm.to_mesh(pl); bm.free()
    pl.materials.append(black)
    col.objects.link(bpy.data.objects.new("Hall_Plaque", pl))
    pi = icon(col, "Hall_Plaque_Icon", white, 0.08)
    facing_plus_x(pi, WALL_X + 0.0135, py - 0.15, pz + 0.10)
    for k, (body, fname, size, dz) in enumerate((("FAB LAB SAGA", "RobotoCondensed-Bold.ttf", 0.045, 0.085),
                                                 ("Háskóli Íslands · Reykjavíkurborg · Mixtúra", "RobotoCondensed-Light.ttf", 0.022, 0.0),
                                                 ("Opið / Open", "RobotoCondensed-Regular.ttf", 0.024, -0.055),
                                                 ("mán-fös 10-18 · lau 12-16", "RobotoCondensed-Light.ttf", 0.022, -0.090))):
        t = text(col, f"Hall_Plaque_T{k}", body, fname, size, white, extrude=0.0005)
        facing_plus_x(t, WALL_X + 0.0125, py - 0.20 if k else py - 0.095, pz + dz)
    # ---- vinyl on the fire-glass panel, hall side
    di = icon(col, "Hall_Door_Icon", vinyl, 0.16)
    facing_plus_x(di, GLASS_X + 0.0015, 35.67, 1.55)
    dt = text(col, "Hall_Door_Text", "FAB LAB SAGA", "RobotoCondensed-Bold.ttf", 0.055, vinyl, extrude=0.0)
    bpy.context.view_layer.update()
    facing_plus_x(dt, GLASS_X + 0.0015, 35.67 - width(dt) / 2, 1.40)
    # ---- camera rename: this is the hall entrance, not an exterior
    cam = bpy.data.objects.get("Cam_ExteriorEntrance")
    if cam:
        cam.name = cam.data.name = "Cam_HallEntrance"
    print("hall entrance signage built")


build()
