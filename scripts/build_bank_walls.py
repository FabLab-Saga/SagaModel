"""Búnaðarbankinn (staff only) closed on all sides, 2.80 m high (open above), with a secret door
facing the entrance hidden in a sculpture. Re-runnable ("BankWalls" collection).

- South wall (workshop side): OSB-faced stud wall y 34.32-34.40, 2.80 m (replaces the
  colleague's single OSB sheet that stopped at 3.05 m with a gap underneath).
- East wall (entrance side): plastered stud wall x 27.49-27.57, y 34.32-38.35, 2.80 m.
  Door opening y 36.62-37.58, 2.40 m high.
- Secret door: a parametric "fin wall" relief of 18 mm birch-ply fins (CNC-cut, 55 mm pitch)
  spanning y 36.50-37.70, rippling in depth; the fins over the opening ride on the door leaf, so the
  door seam disappears between two fins. Front edges of the fins carry a brand-colour sweep.
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
D0, D1, DH = 36.62, 37.58, 2.40     # door opening
F0, F1 = 36.50, 37.70               # sculpture extent


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
    # hide the colleague's OSB sheet (now inside the new wall)
    o = bpy.data.objects.get("osb st2.001")
    if o:
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = True

    # door leaf (plaster panel flush with the wall) + the fins that ride on it
    leaf = Part()
    leaf.box(paint, XW0 + 0.005, XW1, D0 + 0.003, D1 - 0.003, 0.003, DH - 0.003)
    sculpt = Part()
    pitch = 0.055
    n = int((F1 - F0) / pitch)
    for i in range(n + 1):
        y = F0 + i * pitch
        t = i / n
        edge = sweep[min(4, int(t * 5))]
        target = leaf if D0 + 0.01 < y < D1 - 0.03 else sculpt
        fin(target, ply, y, t, 0.06, 2.62, XW1, edge=edge)
    sculpt.emit("SecretDoor_Sculpture", col, Vector((0, 0, 0)))
    leaf.emit("SecretDoor_Leaf", col, Vector((0, 0, 0)))
    # plinth and top cap tie the fins together like a gallery piece
    cap = Part()
    cap.box(MAT["profile"], XW1, XW1 + 0.04, F0 - 0.01, F1 + 0.03, 0.0, 0.06)
    cap.box(MAT["profile"], XW1, XW1 + 0.04, F0 - 0.01, F1 + 0.03, 2.62, 2.66)
    cap.emit("SecretDoor_Frame", col, Vector((0, 0, 0)))
    print("bank walls + secret door built:", n + 1, "fins")


build()


def bank_counter():
    """Sorting / packing counter in the middle of the bank (staff work surface): 2.4 x 0.8 m
    profile table at 0.95 m with a lower shelf; boxes being sorted, a label printer, a laptop,
    a parts tray, kit contents laid out; two stools."""
    col = bpy.data.collections["BankWalls"]
    _c = open(HERE + "build_craft_spine.py").read()
    craft = {}
    exec(_c[:_c.index("\ndef build():")], craft)
    _b = open(HERE + "build_bank_lounge.py").read()
    bank = {}
    exec(_b[:_b.index("\ndef build():")], bank)
    L, D, H = 2.40, 0.80, 0.95
    cx, cy = 24.40, 36.25
    t, _ = lib["table_unit"](L, D, H, [0.0, L - 0.04], lower=(0.16,))
    loc, rot = lib["placement"](cx, cy, L, D, "-y")
    t.emit("Bank_Counter", col, loc, rot)
    p = Part()
    samla = bank["samla"]
    samla(p, 0.15, 0.10, H, 22)                                         # open boxes being sorted
    samla(p, 0.62, 0.10, H, 11)
    samla(p, 0.12, 0.10, 0.16, 65)                                     # under-shelf stock
    samla(p, 0.80, 0.10, 0.16, 65)
    samla(p, 1.45, 0.10, 0.16, 45)
    grey = mat("LabelPrinter", "#2B2D30", 0.4)
    p.box(grey, 1.20, 1.36, 0.45, 0.62, H, H + 0.09, bevel=0.01)                       # label printer
    p.box(mat("Label_Tape", "#F2F1EC", 0.6), 1.22, 1.34, 0.42, 0.45, H + 0.04, H + 0.041)
    lap = bpy.data.materials.get("Laptop_Body") or grey
    p.box(lap, 1.55, 1.87, 0.30, 0.52, H, H + 0.012, bevel=0.003)                      # laptop base
    p.box(lap, 1.55, 1.87, 0.52, 0.525, H + 0.012, H + 0.23, bevel=0.002)              # lid
    p.box(mat("Tray_Grey", "#7C8085", 0.5), 0.70, 1.05, 0.48, 0.70, H, H + 0.03, bevel=0.003)
    for k in range(10):                                                 # kit contents laid out
        x, y = 2.0 + (k % 3) * 0.10, 0.20 + (k // 3) * 0.13
        p.box(MAT["bins"][k % 6], x, x + 0.07, y, y + 0.09, H, H + 0.025, bevel=0.003)
    p.emit("Bank_Counter_Stuff", col, loc, rot)
    for i, sx in enumerate((cx - 0.6, cx + 0.5)):
        craft["stool"](0.68).emit(f"Bank_Stool_{i}", col, Vector((sx - 0.18, cy + D / 2 + 0.12, 0.0)), 0.15 * (i - 0.5))


bank_counter()
