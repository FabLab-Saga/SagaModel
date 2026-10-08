"""Búnaðarbankinn (staff only) closed on all sides, 2.80 m high (open above), with a secret door
facing the entrance hidden in a sculpture. Re-runnable ("BankWalls" collection).

- South wall (workshop side): OSB-faced stud wall y 34.32-34.40, 2.80 m (replaces the
  colleague's single OSB sheet that stopped at 3.05 m with a gap underneath).
- East wall (entrance side): plastered stud wall x 27.49-27.57, y 34.32-38.35, 2.80 m.
  Door opening y 36.62-37.58, 2.40 m high.
- Secret door (Magnús, 2026-10-08: a BOOKCASE door, so it vanishes into the shelf language around it; replaced the
  birch-fin relief, which read as a door-shaped object and clipped its frame when opened): one bay of the spine's
  black-profile + birch shelving, filled with books like the spine's lounge face, on a CENTRE PIVOT. The slot between
  the spine end (y 36.47) and the demo shelving (y 37.70) is 1.23 m and the hex art above starts at z 2.57, so the leaf
  is 1.16 x 0.30 m (swept radius 0.61 m < 0.615 to both neighbours and < 0.625 to the jambs), 2.45 m high; the wall
  opening is y 36.46-37.71 x 2.46. White back panel on the bank side. Animated open in build_walkthrough.py.
- Privacy backs (user): shelf-high (2.42 m) birch-ply panels on the backs of the bank shelving wherever
  outsiders could look in - along the NNE glass (behind run C and across the gaps either side of it) and
  along the ESE back wall (behind runs A1/A2, which has an opening at x 25.7-26.5). The south run B
  already backs onto the 2.80 m south wall.
"""
import math

import bmesh
import bpy
from mathutils import Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
Part, mat, lin = lib["Part"], lib["simple_mat"], lib["lin"]

SOFFIT = 3.93
WALL_H = 2.80                       # stops short of the slab (user): light + air over the top
XW0, XW1 = 27.49, 27.57            # east wall
YS0, YS1 = 34.32, 34.40            # south wall (moved 0.8 m into the electronics area, user)
YN = 38.35                          # back (exterior) wall line
D0, D1, DH = 36.46, 37.71, 2.46     # door opening (bookcase pivot leaf, see docstring)
F0, F1 = 36.50, 37.70               # sculpture extent (= the pivot leaf)
PIVOT = (27.68, 37.085)             # leaf centre in plan: back panel 27.49 .. shelf front 27.87


def fin_depth(t, u):
    """Depth (m) of the fin at position t (0..1 along the sculpture) and height u (0..1)."""
    return 0.05 + 0.17 * (0.5 + 0.5 * math.sin(2 * math.pi * (1.3 * t + 0.9 * u) + 1.2)) * \
        (0.55 + 0.45 * math.sin(math.pi * u))


def fin(p, m, y, t, z0, z1, x0, thick=0.018, edge=None):
    bm = p.bm(m)
    n = 24
    pts = [(x0, z0)] + [(x0 + fin_depth(t, k / n), z0 + (z1 - z0) * k / n) for k in range(n + 1)] + [(x0, z1)]
    a = [bm.verts.new((x, y, z)) for x, z in pts]
    b = [bm.verts.new((x, y + thick, z)) for x, z in pts]
    bm.faces.new(a)
    bm.faces.new(list(reversed(b)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    if edge is not None:                                        # painted front edge strip
        e = p.bm(edge)
        for k in range(n):
            xa, za = pts[k + 1]; xb, zb = pts[k + 2]
            v = [e.verts.new((xa + 0.0006, y - 0.0005, za)), e.verts.new((xb + 0.0006, y - 0.0005, zb)),
                 e.verts.new((xb + 0.0006, y + thick + 0.0005, zb)), e.verts.new((xa + 0.0006, y + thick + 0.0005, za))]
            e.faces.new(v)


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("BankWalls") or bpy.data.collections.new("BankWalls")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    paint = bpy.data.materials["Paint_White"]
    osb = bpy.data.materials["OSB"]
    ply = MAT["ply"]
    shadow = mat("Seam_Shadow", "#080808", 0.9)
    sweep = [mat(f"Fin_Edge_{i}", h, 0.5) for i, h in enumerate(("#E03A3F", "#FFA13D", "#F2C200", "#009967", "#1245DE"))]

    w = Part()
    # south wall: OSB faced both sides, floor to soffit
    w.box(osb, 20.90, XW1, YS0, YS1, 0.0, WALL_H)
    # east wall in three pieces around the door opening
    w.box(paint, XW0, XW1, YS0, D0, 0.0, WALL_H)
    w.box(paint, XW0, XW1, D1, YN, 0.0, WALL_H)
    w.box(paint, XW0, XW1, D0, D1, DH, WALL_H)
    # hairline seams around the leaf (visible only between fins)
    w.box(shadow, XW1, XW1 + 0.001, D0 - 0.003, D0, 0.0, DH)
    w.box(shadow, XW1, XW1 + 0.001, D1, D1 + 0.003, 0.0, DH)
    w.box(shadow, XW1, XW1 + 0.001, D0, D1, DH, DH + 0.003)
    w.emit("Bank_Walls", col, Vector((0, 0, 0)))
    # privacy backs on the shelving, shelf-high, held by 40x40 posts at the ends and every ~1.25 m
    SH = 2.42
    pb = Part()
    pb.box(ply, 21.022, 21.040, YS1, YN - 0.02, 0.0, SH, bevel=0.001)                 # NNE glass side
    pb.box(ply, 21.040, XW0, 38.331, 38.349, 0.0, SH, bevel=0.001)                    # ESE back wall side
    for y in (YS1, 35.62, 37.70):                                                       # posts in the gaps by the glass
        pb.profile(0.04, "z", 20.982, min(y, YN - 0.06), 0.0, SH)
    pb.box(MAT["profile"], 20.982, 21.040, YS1, YN - 0.02, SH, SH + 0.02)              # top capping
    pb.box(MAT["profile"], 21.040, XW0, 38.331, 38.349, SH, SH + 0.02)
    pb.emit("Bank_PrivacyBacks", col, Vector((0, 0, 0)))
    # hide the colleague's OSB sheet (now inside the new wall)
    o = bpy.data.objects.get("osb st2.001")
    if o:
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = True

    # bookcase pivot leaf: everything built in world space, then parented to the pivot empty "SecretDoor_Leaf"
    px, py = PIVOT
    for o in ("SecretDoor_Leaf", "SecretDoor_Sculpture", "SecretDoor_Frame", "SecretDoor_Hinge"):
        ob = bpy.data.objects.get(o)
        if ob:
            for k in list(ob.children_recursive) + [ob]:
                if k.name in bpy.data.objects:
                    bpy.data.objects.remove(k)
    sp = {}
    _c = open(HERE + "build_craft_spine.py").read()
    exec(_c[:_c.index("\ndef build():")], sp)                    # book(), books_and_plants(), shelf language
    lv = [0.10, 0.48, 0.86, 1.24, 1.62, 2.00]                        # = the spine's shelf levels
    part, slots, L = lib["shelf_unit"]([1.08], 0.30, 2.42, lv)        # L = 1.16
    loc, rot = lib["placement"](XW1 + 0.15, py, L, 0.30, "+x")
    fill = sp["Part"]()
    tops = lv + [2.42]
    for (bi, li), (xa, xb, _, _, zt) in slots.items():
        sp["books_and_plants"](fill, xa, xb, 0.30, zt, tops[li + 1] - zt - 0.06, (loc, rot))
    back = Part()
    back.box(paint, XW0 + 0.002, XW1, py - L / 2, py + L / 2, 0.003, DH - 0.006)            # bank-side face
    back.box(ply, XW1, XW1 + 0.012, py - L / 2 + 0.04, py + L / 2 - 0.04, 0.04, 2.40)       # birch back of the bay
    piv = bpy.data.objects.new("SecretDoor_Leaf", None)
    col.objects.link(piv)
    piv.location, piv.empty_display_size = (px, py, 0.0), 0.3
    roots = [part.emit("SecretDoor_Shelf", col, loc, rot), fill.emit("SecretDoor_Books", col, loc, rot),
             back.emit("SecretDoor_Back", col, Vector((0, 0, 0)))]
    bpy.context.view_layer.update()
    for r in roots:
        mw = r.matrix_world.copy()
        r.parent = piv
        r.matrix_parent_inverse = piv.matrix_world.inverted()
        r.matrix_world = mw
    print("bank walls + bookcase secret door built")


build()

