"""Fab Lab SAGA keyring tag, ported from the teaching wiki's print-cycle job (prusa-wiki research/gcode-print/
make-tag.py on the coordinator host, original geometry): base 58 x 24 x 3.0 mm with 5 mm corner radii and a 5.5 mm
ring hole, the word SAGA standing 1.2 mm proud, cap height 11 mm, centred 4 mm right of the tag centre. Port change
(mine): Roboto Bold (the project's brand font, refs/branding/fonts) instead of IBM Plex Sans SemiBold.

    exec(open(HERE + "saga_tag.py").read(), ns);  ns["saga_tag_mesh"](raise_mm=1.2) -> bpy.types.Mesh (metres, base on z=0)
"""
import math

import bpy

TAG_W, TAG_D, TAG_BASE, TAG_RAISE, TAG_R, TAG_HOLE = 0.058, 0.024, 0.003, 0.0012, 0.005, 0.0055


def _poly_spline(cu, pts):
    sp = cu.splines.new("POLY")
    sp.points.add(len(pts) - 1)
    for p, (x, y) in zip(sp.points, pts):
        p.co = (x, y, 0.0, 1.0)
    sp.use_cyclic_u = True


def _curve_to_mesh(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    return me


def saga_tag_mesh(raise_mm=1.2, name="SAGA_Tag"):
    """Closed tag mesh (base + raised lettering up to raise_mm, so a print in progress can stop part-way)."""
    key = f"{name}_{raise_mm:.2f}"
    if key in bpy.data.meshes:
        return bpy.data.meshes[key]
    import bmesh
    scene_col = bpy.context.scene.collection
    # base: rounded rectangle with the ring hole (2D curve, even-odd fill), extruded
    cu = bpy.data.curves.new(key + "_base", "CURVE")
    cu.dimensions, cu.fill_mode = "2D", "BOTH"
    pts = []
    for cx, cy, a0 in ((TAG_W / 2 - TAG_R, TAG_D / 2 - TAG_R, 0), (-TAG_W / 2 + TAG_R, TAG_D / 2 - TAG_R, 90),
                       (-TAG_W / 2 + TAG_R, -TAG_D / 2 + TAG_R, 180), (TAG_W / 2 - TAG_R, -TAG_D / 2 + TAG_R, 270)):
        for k in range(13):
            a = math.radians(a0 + 90 * k / 12)
            pts.append((cx + TAG_R * math.cos(a), cy + TAG_R * math.sin(a)))
    _poly_spline(cu, pts)
    hx = -TAG_W / 2 + 0.0065
    _poly_spline(cu, [(hx + TAG_HOLE / 2 * math.cos(2 * math.pi * k / 32), TAG_HOLE / 2 * math.sin(2 * math.pi * k / 32))
                      for k in range(32)])
    cu.extrude = TAG_BASE / 2
    ob = bpy.data.objects.new(key + "_base", cu)
    scene_col.objects.link(ob)
    ob.location.z = TAG_BASE / 2
    # lettering
    tc = bpy.data.curves.new(key + "_txt", "FONT")
    f = bpy.data.fonts.get("Roboto-Bold") or bpy.data.fonts.load(bpy.path.abspath("//refs/branding/fonts/Roboto-Bold.ttf"))
    tc.body, tc.font, tc.align_x, tc.align_y = "SAGA", f, "CENTER", "CENTER"
    tc.size = 0.011 / 0.711                                            # Roboto cap height 0.711 em -> 11 mm caps
    tc.extrude = raise_mm / 2000.0
    tc.resolution_u = 6
    to = bpy.data.objects.new(key + "_txt", tc)
    scene_col.objects.link(to)
    to.location = (0.004, 0.0, TAG_BASE + raise_mm / 2000.0)
    bpy.context.view_layer.update()
    bm = bmesh.new()
    for o in (ob, to):
        me = _curve_to_mesh(o)
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    for o, c in ((ob, cu), (to, tc)):
        bpy.data.objects.remove(o)
        bpy.data.curves.remove(c)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    me = bpy.data.meshes.new(key)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    return me
