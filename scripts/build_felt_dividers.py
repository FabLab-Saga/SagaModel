"""Mobile felt dividers (collection FeltDividers). Re-runnable; run after build_microelectronics.

Magnús (2026-11-25): the tool walls the three Flöff felt panels hung on are gone; the panels become movable screens,
"the three existing 2 m panels on castor frames, gap at the column", "Each panel separated. This is their 'Default'
spot but they're intended to be movable to block specific noise or divide the area depending on our needs."
My design: each panel keeps its felt mesh (Floff_Panel_1..3, arched tops on the manual's grid, unchanged) and gets
its own black 40x40 frame: two posts at the panel ends, a bottom rail under the felt, two 0.50 m feet set in 0.20 m
from the ends, four locking castors. Default spot = the old row line (felt plane y ~29.765), panels slid towards the
NNE glass with 0.08 m between frames so each stands alone. Magnús moved the default line 0.30 m towards the workshop
(2026-11-25) to make room for the electronics re-layout; that also clears the column at (27.61, 30.16).
Each panel is its own layout item (movable in Blender or the planner).
"""
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
Part = lib["Part"]

PANELS = ["Floff_Panel_1", "Floff_Panel_2", "Floff_Panel_3"]
X_START, GAP, POST = 21.50, 0.04, 0.04           # start past the cutter counter's end (x 21.45)
YC = 29.465                                          # felt mid-plane: old row line moved 0.30 m towards the workshop (Magnús)
DY = [0.0, 0.0, 0.0]
FOOT, SETIN, CASTOR = 0.50, 0.20, 0.09
SETIN_END = {2: 0.30}                               # panel 3's column-end foot set in further (column at x 27.61)


def clear(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        if o.name in PANELS:
            continue
        d = o.data
        bpy.data.objects.remove(o)
        if isinstance(d, bpy.types.Mesh) and d.users == 0:
            bpy.data.meshes.remove(d)
    return col


def mesh_bounds(me):
    xs = [v.co.x for v in me.vertices]; zs = [v.co.z for v in me.vertices]
    x0, x1 = min(xs), max(xs)
    end_h = max(v.co.z for v in me.vertices if abs(v.co.x - x0) < 0.01)
    return x0, x1, min(zs), end_h


def build():
    col = clear("FeltDividers")
    blk = MAT["profile"]
    x = X_START
    for i, n in enumerate(PANELS):
        yc = YC + DY[i]
        o = bpy.data.objects.get(n)
        if o is None:
            print("missing", n); continue
        for c in list(o.users_collection):                                   # move the felt into this collection
            if c != col:
                c.objects.unlink(o)
        if o.name not in col.objects:
            col.objects.link(o)
        o.parent = None
        mx0, mx1, mz0, end_h = mesh_bounds(o.data)                            # mesh is in world coords at origin
        w = mx1 - mx0
        fx0 = x + POST                                                        # felt starts after the left post
        my = sum(v.co.y for v in o.data.vertices) / len(o.data.vertices)      # felt mid-plane in the mesh
        o.matrix_world = Matrix.Translation((fx0 - mx0, yc - my, 0.0))
        f = Part()
        y0 = yc - POST / 2
        for px in (fx0 - POST, fx0 + w):
            f.profile(POST, "z", px, y0, CASTOR + 0.04, end_h - CASTOR - 0.04)    # posts (from the feet up)
        f.profile(POST, "x", fx0 - POST, y0, mz0 - POST, w + 2 * POST)            # bottom rail under the felt
        for px in (fx0 + SETIN - POST, fx0 + w - SETIN_END.get(i, SETIN)):
            f.profile(POST, "y", px, yc - FOOT / 2, CASTOR, FOOT)                 # feet
            for py in (yc - FOOT / 2 + 0.03, yc + FOOT / 2 - 0.03):              # locking castors
                cx = px + POST / 2
                f.cyl(blk, (cx, py, CASTOR - 0.005), (cx, py, CASTOR - 0.02), 0.018, seg=12)      # swivel plate
                f.cyl(MAT["foot"], (cx - 0.012, py, 0.035), (cx + 0.012, py, 0.035), 0.035, seg=18)  # wheel
                f.box(lib["simple_mat"]("Castor_Brake_Red", "#C8102E", 0.4), cx + 0.012, cx + 0.03, py - 0.01,
                      py + 0.01, 0.05, 0.06)                                                    # brake pedal
        fr = f.emit(f"FeltFrame_{i + 1}", col, Vector((0, 0, 0)))
        o.parent = fr
        o.matrix_parent_inverse = fr.matrix_world.inverted()
        x = fx0 + w + POST + GAP
    print("felt dividers: 3 mobile panels, line ends at x %.3f" % (x - GAP))


build()

_lay = {}
exec(open(bpy.path.abspath("//scripts/layout_blender.py")).read(), _lay)
_lay["apply"]("FeltDividers")
