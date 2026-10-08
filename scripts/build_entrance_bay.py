"""Entrance corner bay + the university hall outside the Fab Lab door. Re-runnable: rebuilds the collections
"EntranceBay" and "Hall" and the Cut_EntranceWall boolean on ROOT.geo0.

Facts (city drawings, Andrúm SAGA AT 20-10-02 ground-floor plan, approved 2026-06-30, case USK26040333; research
in ~/Documents/AgentWork/saga-video/hall/HALL.md; fix approved by Magnús 2026-10-08):
- The lab ("háskóli 01-02") includes the corner bay x 32.6-34.3, y 34.6-38.3 that the colleague's model left as
  outdoor paving. The colleague's entrance wall at x 32.43-32.63 (door y 35.11-36.21 + side window) does not exist.
- The entrance is in the bay's SSW wall (line x ~34.31): a single-leaf fire door EI2 30-CS200, opening y 36.54-37.47
  (~0.93 m), hinged at the ESE jamb, swinging INTO the lab. WNW of it: a pier, a fixed EI30 fire-glass panel at
  y ~35.0-36.3, and a pier down to the façade corner (y 34.6). ESE of it: an EI60 wall that wraps column (33.60,
  38.55) and runs on to stair core D.
- Outside the door is an interior hall "háskóli 01-01" at the same floor level: glass façade along y ~34.7 (camera
  facing the door has it on the LEFT), exterior double door in it at x ~40.5-42.5, a freestanding WC box (2 WCs) at
  x ~36.3-39.4, y ~38.7-42.6 with a check-in desk, stair D / lifts / cleaners' cupboard behind the door wall to the
  ESE, a teaching-room wall at y ~45, free-standing round columns at x 44.8 (y 38.55, 44.75), seating groups along the
  glass (x 37-40, y 35.5-36.5). Floor to floor 4.2 m.
Finishes (my inference from photos of the main lobby + Háma servery; not in the drawings): dark grey-green polished
stone floor, white 600x600 acoustic ceiling at 3.10 m with square LED panels, white walls, round white columns.
Door leaf: birch veneer like the other doors (my choice; the drawing only gives the fire rating), held open on its
magnet. Everything else in the hall is a SET for the film: only what the camera sees.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
_s = open(HERE + "build_staff_area.py").read()
sa = {}
exec(_s[:_s.index("\ndef build():")], sa)                          # Part, door_in_wall, door, plaque, tile, mats
Part, mat, tile, lin = sa["Part"], sa["mat"], sa["tile"], sa["lin"]
SOFFIT = 3.93

# bay + door wall (model frame)
OLD_WALL = (32.40, 32.68)                 # colleague's entrance wall (x) to cut away
BAY_Y = (34.705, 38.325)                  # between the bay's WNW wall (ends y 34.70) and the lab's back wall face
WALL = (34.24, 34.44)                     # new door wall: lab face / hall face (colleague pier + slab edge at 34.44)
PIER_END = 35.04                          # colleague's pier y 34.44-35.04
GLASS = (35.04, 36.30)                    # fixed EI30 fire glass
DOOR = (36.54, 37.47)                     # door opening
WRAP_Y1 = 38.95                           # wall wraps column (33.60, 38.55)
BACK = (38.325, 38.60)                    # bay's ESE wall (lab face 38.325)
HEAD = 2.12
# hall set
HX1, HY0, HY1 = 47.0, 34.70, 45.20
CEIL = 3.10


def clear(name):
    return sa["clear_collection"](name)


def cutter(name, x0, x1, y0, y1, z0=-0.05, z1=3.94):
    cut_col = bpy.data.collections["Facade_Cutters"]
    me = bpy.data.meshes.get(name) or bpy.data.meshes.new(name)
    bm = bmesh.new()
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((x1 if v.co.x > 0 else x0, y1 if v.co.y > 0 else y0, z1 if v.co.z > 0 else z0))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, me)
    if ob.name not in cut_col.objects:
        cut_col.objects.link(ob)
    ob.display_type, ob.hide_render = "WIRE", True
    ob.hide_set(True)
    root = bpy.data.objects["ROOT.geo0"]
    mod = root.modifiers.get(name) or root.modifiers.new(name, "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", ob


def delete_colleague_parts():
    """The colleague's side window in the (non-existent) entrance wall."""
    n = 0
    for o in list(bpy.data.objects):
        if o.name in ("WINDOW.geo0.028", "WINDOW.geo2.028"):
            data = o.data
            bpy.data.objects.remove(o)
            if isinstance(data, bpy.types.Mesh) and data.users == 0:
                bpy.data.meshes.remove(data)
            n += 1
    return n


# ------------------------------------------------------------------ lab side: bay, door wall, door
def bay(col):
    white = bpy.data.materials["Paint_White"]
    frame = mat("Steel_Frame_White", "#E9E9E6", 0.35, metal=0.2)
    gl = bpy.data.materials["Glass_Clear"]
    cutter("Cut_EntranceWall", OLD_WALL[0], OLD_WALL[1], BAY_Y[0], BAY_Y[1])
    p, g = Part(), Part()
    p.box(bpy.data.materials["Parquet"], 32.59, WALL[0] + 0.005, BAY_Y[0] - 0.005, BAY_Y[1], -0.25, 0.0)   # floor
    p.box(white, 32.62, WALL[0], BACK[0], BACK[1], 0.0, SOFFIT)                     # bay's ESE wall
    w0, w1 = WALL
    wc = (w0 + w1) / 2
    p.box(white, w0, w1, GLASS[1], DOOR[0], 0.0, SOFFIT)                           # pier between glass and door
    p.box(white, w0, w1, DOOR[1], WRAP_Y1, 0.0, SOFFIT)                            # wall ESE of the door (wraps column)
    p.box(white, w0, w1, GLASS[0], GLASS[1], HEAD, SOFFIT)                         # wall above the fire glass
    F = 0.05                                                                       # fire-glass frame (steel, white)
    for a, b in ((GLASS[0], GLASS[0] + F), (GLASS[1] - F, GLASS[1])):
        p.box(frame, w0 - 0.01, w1 + 0.01, a, b, 0.0, HEAD)
    p.box(frame, w0 - 0.01, w1 + 0.01, GLASS[0], GLASS[1], HEAD - F, HEAD)
    p.box(frame, w0 - 0.01, w1 + 0.01, GLASS[0], GLASS[1], 0.0, 0.10)
    g.box(gl, wc - 0.0005, wc + 0.0005, GLASS[0] + F, GLASS[1] - F, 0.10, HEAD - F)
    p.emit("Entrance_Bay", col, Vector((0, 0, 0)))
    g.emit("Entrance_FireGlass", col, Vector((0, 0, 0)))
    # door: frame + casings + wall above (helper), leaf held open ~90 deg into the lab (hinge at the ESE jamb)
    sa["door_in_wall"](col, "Entrance_Door", "y", wc, w1 - w0, DOOR[0], DOOR[1], -1, 1, angle=88.0, H=HEAD,
                       leaf=DOOR[1] - DOOR[0] - 2 * 0.045 - 0.006)
    hold = Part()                                                                  # floor-mounted magnetic hold-open
    hold.cyl(mat("Fitting_Grey", "#9A9C9E", 0.4), (33.40, 37.40, 0.0), (33.40, 37.40, 0.07), 0.025, seg=16)
    hold.emit("Entrance_Door_Holder", col, Vector((0, 0, 0)))
    # exit sign above the door, lab side
    e = Part()
    e.box(mat("Fitting_White", "#F2F1EE", 0.35), w0 - 0.04, w0, 36.70, 37.30, 2.22, 2.40, bevel=0.004)
    e.box(mat("Exit_Green", "#1E9E52", 0.3, emit=2.0), w0 - 0.045, w0 - 0.04, 36.74, 37.26, 2.24, 2.38)
    e.emit("Entrance_ExitSign", col, Vector((0, 0, 0)))


# ------------------------------------------------------------------ hall set
def hall_mats():
    M = {}
    M["stone"] = tile("Stone_Hall_GreenGrey", "#3C4641", "#2F3632", 0.80, "xy")
    ceil = tile("Ceiling_Acoustic_600", "#F1F1EF", "#CFCFCC", 0.60, "xy")
    mr = next(n for n in ceil.node_tree.nodes if n.type == "MAP_RANGE")
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = 0.85, 0.6
    M["ceil"] = ceil
    M["white"] = bpy.data.materials["Paint_White"]
    M["frame"] = bpy.data.materials["Alu_Frame_Dark"]
    M["glass"] = bpy.data.materials["Glass_Clear"]
    M["panel"] = mat("LED_Panel_Opal", "#FFFFFF", 0.5, emit=3.0)
    M["table"] = mat("Table_White_Laminate", "#F0F0EC", 0.3)
    M["black"] = mat("Cart_Black", "#1F1F20", 0.45, metal=0.3)
    M["oak"] = mat("Oak_Chair", "#B48A5A", 0.45)
    M["door"] = bpy.data.materials.get("Door_Birch_Veneer") or mat("Door_Birch_Veneer", "#D9C29E", 0.45)
    M["concrete"] = bpy.data.materials.get("Concrete_Exposed") or M["white"]
    return M


def hall(col, M):
    p, g, lights = Part(), Part(), []
    x0 = WALL[1]
    # floor, ceiling (acoustic grid) with LED panels, soffit of the covered outdoor strip
    p.box(M["stone"], x0, HX1, HY0, HY1, -0.25, 0.0)
    p.box(M["ceil"], x0, HX1, HY0, HY1, CEIL, CEIL + 0.02)
    p.box(M["white"], x0, HX1, HY0, HY1, CEIL + 0.02, SOFFIT)                    # plenum box (keeps the sky out)
    for cx in (35.9, 38.3, 40.7, 43.1, 45.5):
        for cy in (36.1, 38.5, 40.9, 43.3):
            if 36.2 < cx < 39.5 and 38.6 < cy < 42.7:                            # not over the WC box
                continue
            p.box(M["panel"], cx - 0.29, cx + 0.29, cy - 0.29, cy + 0.29, CEIL - 0.004, CEIL)
            lights.append((cx, cy))
    p.box(M["concrete"], x0, HX1, 31.8, HY0, 3.62, 3.92)                          # outdoor canopy (upper floors)
    # door wall continues ESE (stair D / lifts) to the NNE wall; cleaners' cupboard box with a door
    p.box(M["white"], x0 - 0.20, x0, WRAP_Y1, HY1, 0.0, CEIL)
    p.box(M["white"], x0, x0 + 0.62, 39.25, 41.60, 0.0, CEIL)
    sa["door"](col, "Hall_CleanersDoor", (x0 + 0.62, 39.40), 0.80, (0.0, 1.0), 0.0)
    p.box(M["white"], x0, HX1, HY1 - 0.20, HY1, 0.0, CEIL)                        # teaching-room wall (NNE end)
    # glass façade along y 34.70 (camera facing the door: on the left) with the exterior double door
    yg = HY0
    xs = [x0 + 0.03]
    while xs[-1] < HX1 - 0.1:
        xs.append(min(xs[-1] + 1.50, HX1))
    D0, D1 = 40.5, 42.5
    xs = [x for x in xs if not (D0 - 0.2 < x < D1 + 0.2)] + [D0, D1]
    xs.sort()
    for x in xs:
        p.box(M["frame"], x - 0.03, x + 0.03, yg - 0.06, yg + 0.06, 0.0, CEIL)    # mullions
    p.box(M["frame"], x0, HX1, yg - 0.06, yg + 0.06, 0.0, 0.06)                   # sill
    p.box(M["frame"], x0, HX1, yg - 0.06, yg + 0.06, CEIL - 0.08, CEIL)          # head
    p.box(M["frame"], D0, D1, yg - 0.06, yg + 0.06, 2.30, 2.36)                  # door transom
    for a, b in zip(xs, xs[1:]):
        za = 0.06
        if a == D0:                                                               # door leaves: framed glass + push bars
            mid = (D0 + D1) / 2
            p.box(M["frame"], mid - 0.03, mid + 0.03, yg - 0.05, yg + 0.05, 0.0, 2.30)
            for lx0, lx1 in ((D0 + 0.03, mid - 0.03), (mid + 0.03, D1 - 0.03)):
                p.box(M["frame"], lx0, lx1, yg - 0.04, yg + 0.04, 0.0, 0.12)
                g.box(M["glass"], lx0, lx1, yg - 0.0005, yg + 0.0005, 0.12, 2.30)
                p.cyl(bpy.data.materials["Steel_Brushed"], (lx0 + 0.08, yg + 0.09, 1.0), (lx1 - 0.08, yg + 0.09, 1.0), 0.016)
            g.box(M["glass"], D0 + 0.03, D1 - 0.03, yg - 0.0005, yg + 0.0005, 2.36, CEIL - 0.08)
            continue
        g.box(M["glass"], a + 0.03, b - 0.03, yg - 0.0005, yg + 0.0005, za, CEIL - 0.08)
    # free-standing round columns
    for cx, cy in ((44.80, 38.55), (44.80, 44.75)):
        p.cyl(M["white"], (cx, cy, 0.0), (cx, cy, CEIL), 0.33, seg=40)
    # WC box with two doors facing WNW (the hall), "WC" plaques
    bx0, bx1, by0, by1 = 36.30, 39.40, 38.70, 42.60
    p.box(M["white"], bx0, bx1, by0, by1, 0.0, CEIL)
    for k, (dx0, w) in enumerate(((36.70, 0.90), (38.30, 0.80))):
        sa["door"](col, f"Hall_WC_Door_{k + 1}", (dx0, by0 - 0.02), w, (1.0, 0.0), 0.0)
        sa["plaque"](col, f"Hall_WC_{k + 1}", "WC", (dx0 + w + 0.18, by0, 1.55), (0.0, -1.0), w=0.14, h=0.14, size=0.06)
    # check-in kiosk by the WC box: standing desk + screen
    k = Part()
    k.box(M["table"], 39.75, 40.65, 39.20, 39.75, 0.0, 1.05, bevel=0.01)
    k.box(M["black"], 40.05, 40.40, 39.45, 39.48, 1.05, 1.32)
    k.box(bpy.data.materials["Glass_BlackGloss"], 40.07, 40.38, 39.444, 39.45, 1.07, 1.30)
    k.emit("Hall_CheckIn", col, Vector((0, 0, 0)))
    # seating groups along the glass: round tables + chairs
    for tx, ty in ((37.6, 36.0), (39.4, 36.2)):
        t = Part()
        t.cyl(M["table"], (0, 0, 0.71), (0, 0, 0.74), 0.36, seg=40)
        t.cyl(M["black"], (0, 0, 0.0), (0, 0, 0.71), 0.03, seg=16)
        t.cyl(M["black"], (0, 0, 0.0), (0, 0, 0.02), 0.25, seg=32)
        t.emit(f"Hall_Table_{tx:.0f}", col, Vector((tx, ty, 0)))
        for a in (0, 120, 240):
            r = math.radians(a + (30 if tx > 38 else 0))
            c = Part()
            c.box(M["oak"], -0.21, 0.21, -0.20, 0.20, 0.44, 0.47, bevel=0.01)
            c.box(M["oak"], -0.20, 0.20, 0.17, 0.20, 0.50, 0.82, bevel=0.01)
            for sx in (-0.18, 0.18):
                for sy in (-0.17, 0.17):
                    c.cyl(M["black"], (sx, sy, 0.0), (sx, sy, 0.44), 0.011, seg=8)
            c.emit(f"Hall_Chair_{tx:.0f}_{a}", col, Vector((tx + 0.62 * math.cos(r), ty + 0.62 * math.sin(r), 0)),
                   r + math.pi / 2)
    p.emit("Hall_Shell", col, Vector((0, 0, 0)))
    g.emit("Hall_Glass", col, Vector((0, 0, 0)))
    for i, (cx, cy) in enumerate(lights):                                       # panel light sources
        ld = bpy.data.lights.new(f"Hall_Panel_{i}", "AREA")
        ld.shape, ld.size, ld.energy, ld.color = "SQUARE", 0.58, 55.0, (1.0, 0.97, 0.92)
        lo = bpy.data.objects.new(f"Hall_Panel_{i}", ld)
        lo.location = (cx, cy, CEIL - 0.01)
        col.objects.link(lo)


def build():
    n = delete_colleague_parts()
    sa["mats"]()
    bay(clear("EntranceBay"))
    hall(clear("Hall"), hall_mats())
    cam = bpy.data.objects.get("Cam_HallEntrance")                                # still: hall view of the door
    if cam:
        eye, tgt = Vector((40.6, 36.4, 1.62)), Vector((34.44, 36.8, 1.45))
        cam.location = eye
        cam.rotation_euler = (math.pi / 2, 0.0, math.atan2(tgt.y - eye.y, tgt.x - eye.x) - math.pi / 2)
        cam.data.lens, cam.data.shift_y = 24, 0.0
    print(f"entrance bay + hall set built ({n} colleague parts deleted)")


build()
