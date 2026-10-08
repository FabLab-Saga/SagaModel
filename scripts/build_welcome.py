"""Entrance / lounge: the on-call desk and the FabLabTV screen. Re-runnable ("Welcome" collection).
Model frame: +X = SSW (entrance door on the SSW glazing at x 32.5, y 35.11-36.21), +Y = ESE.

- On-call desk (NOT a reception counter): one person's sitting desk with its back to the spine bookcase, facing the
  entrance door: whoever is on call sees everyone who comes in (door straight ahead) and the lounge and the corridor
  down to the workshop (front-left), without turning round. The monitor faces the sitter, so its screen is never
  visible from the door. A raised birch ledge (1.05 m) with a birch modesty panel runs along the door-facing front and
  wraps the corridor end, so the desk top is screened from passers-by; visitors meet the ledge. Monitor, laptop,
  phone, a small "On call" tent card + sign-in tablet on the ledge, mug, notebook. Profile chair. The monitor sits on
  the corridor side so it never blocks the sitter's line of sight to the door.
- TV: one of the equipment list's 80-90" screens, 85" panel wall-mounted on the spine above the on-call desk, facing
  the door: the first thing you see when you walk in. Shows Fab Lab TV (github.com/FabLabReykjavik/FabLabTV, MIT,
  Fab Lab Reykjavik) - a real capture of its /screen page (assets/fablabtv/fablabtv_screen.png: our own print-farm
  render playing as a local video, Neil Gershenfeld on call).
Clearances: >= 1.2 m between the desk's ledge corner and the nook (corridor to the lab); secret-door zone
(x < 28.8, y 36.3-37.9) and the entrance zone free.
"""
import math

import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_m = open(HERE + "build_machines.py").read()
mach = {}
exec(_m[:_m.index("\ndef build():")], mach)
mach["materials"]()
M = mach["M"]
_t = open(HERE + "build_textile.py").read()
tex = {}
exec(_t[:_t.index("\ndef build():")], tex)                         # chair()
mat, Part = lib["simple_mat"], lib["Part"]

TV_C = Vector((28.24, 34.95, 1.98))                                 # wall-mounted panel centre on the spine face
DESK = dict(x0=28.95, x1=29.65, y0=34.15, y1=35.75, h=0.75)        # sitting desk (person on the spine side, -x)
LEDGE_H, LEDGE_D = 1.05, 0.26


def clear_collection(name):
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    return col


def screen_material():
    """TV panel: Fab Lab TV capture as emission + a glossy dark glass coat."""
    m = bpy.data.materials.get("FabLabTV_Screen") or bpy.data.materials.new("FabLabTV_Screen")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out, b = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled")
    img = bpy.data.images.load(bpy.path.abspath("//assets/fablabtv/fablabtv_screen.png"), check_existing=True)
    t = N("ShaderNodeTexImage")
    t.image, t.interpolation = img, "Cubic"
    L(N("ShaderNodeTexCoord").outputs["UV"], t.inputs["Vector"])
    b.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["Coat Weight"].default_value = 0.6
    L(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 2.2
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = (0.05, 0.05, 0.06, 1)
    return m


def tv_wall(col):
    """85" panel (1.89 x 1.07, 3 cm bezel) on a flat wall bracket bolted to the spine's front uprights, facing +x."""
    p = Part()
    blk = mat("Cart_Black", "#1F1F20", 0.45, metal=0.3)
    sw, sh = 1.89, 1.07
    for x in (-0.40, 0.40):
        p.box(blk, x - 0.02, x + 0.02, 0.0, 0.04, -0.30, 0.30)                              # bracket rails
    p.box(blk, -0.42, 0.42, 0.0, 0.04, -0.02, 0.02)
    p.box(M["black"], -sw / 2, sw / 2, 0.04, 0.10, -sh / 2, sh / 2, bevel=0.006)          # panel body
    p.box(M["black"], 0.20, 0.32, 0.0, 0.04, -0.50, -0.38, bevel=0.004)                   # media box behind
    root = p.emit("TV_Wall", col, Vector((0, 0, 0)))
    me = bpy.data.meshes.new("TV_Screen_Face")
    hw, hh, yf = sw / 2 - 0.012, sh / 2 - 0.012, 0.1005                # screen on the +y face (viewer at +y)
    me.from_pydata([(hw, yf, -hh), (-hw, yf, -hh), (-hw, yf, hh), (hw, yf, hh)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new()
    for li, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[li].uv = (u, v)
    me.materials.append(screen_material())
    face = bpy.data.objects.new("TV_Screen_Face", me)
    col.objects.link(face)
    face.parent = root
    root.matrix_world = Matrix.Translation(TV_C) @ Matrix.Rotation(-math.pi / 2, 4, "Z")     # local +y -> world +x
    return root


def oncall_desk(col):
    d = DESK
    L, D = d["y1"] - d["y0"], d["x1"] - d["x0"]
    # sitting desk, local x along the desk (+y world), front (-y local) faces +x world (the door); x = 0 is the
    # corridor end (towards the nook / lab)
    part, _ = lib["table_unit"](L, D, d["h"], [0.0, L - 0.04], lower=())
    loc, rot = lib["placement"]((d["x0"] + d["x1"]) / 2, (d["y0"] + d["y1"]) / 2, L, D, "+x")
    # raised ledge + modesty panel on the door-facing front (local y < 0)
    for x in (0.0, L / 2 - 0.02, L - 0.04):
        part.profile(0.04, "z", x, -0.05, 0.035, LEDGE_H - 0.018 - 0.035)
        lib["foot"](part, x + 0.02, -0.03)
    part.profile(0.04, "x", 0.04, -0.05, LEDGE_H - 0.058, L - 0.08)
    lib["board"](part, -0.02, L + 0.02, -0.05 - LEDGE_D + 0.04, -0.01, LEDGE_H, t=0.025)          # birch ledge
    part.box(MAT["ply"], 0.0, L, -0.052, -0.040, 0.12, LEDGE_H - 0.06)                           # modesty panel
    part.box(MAT["ply"], L, L + 0.012, -0.05, D * 0.55, 0.12, LEDGE_H - 0.06)                    # side return (far end)
    # the ledge wraps the corridor end (local x = 0): people walking past to the lab don't see the desk top
    e = -LEDGE_D                                                     # outer face of the end ledge
    for y in (-0.05, D - 0.04):
        part.profile(0.04, "z", e, y, 0.035, LEDGE_H - 0.018 - 0.035)
        lib["foot"](part, e + 0.02, y + 0.02)
    part.profile(0.04, "y", e, -0.01, LEDGE_H - 0.058, D - 0.03)
    lib["board"](part, e - 0.02, 0.0, -0.05 - LEDGE_D + 0.04, D + 0.02, LEDGE_H, t=0.025)
    part.box(MAT["ply"], e - 0.012, e, -0.05, D, 0.12, LEDGE_H - 0.06)                             # end panel
    part.emit("OnCall_Desk", col, loc, rot)

    def at(lx, ly, z):                                               # desk-local -> world
        return lib["to_world"](loc, rot, (lx, ly, 0)) + Vector((0, 0, z))
    T = d["h"]
    s = Part()
    blk, scr = M["black"], mat("Monitor_Screen", "#1A2430", 0.12, emit=0.5)
    # 27" monitor on the corridor side of the desk (left of the sitter's line to the door), screen facing the
    # sitter (+y local), turned a little towards them; its back faces the door/ledge
    mx = L * 0.24
    s.box(blk, mx - 0.31, mx + 0.31, 0.22, 0.245, T + 0.16, T + 0.52, bevel=0.006)
    s.box(scr, mx - 0.30, mx + 0.30, 0.245, 0.247, T + 0.17, T + 0.51)
    s.cyl(blk, (mx, 0.20, T), (mx, 0.20, T + 0.30), 0.015, seg=12)
    s.box(blk, mx - 0.10, mx + 0.10, 0.12, 0.27, T, T + 0.01, bevel=0.004)
    # laptop (closed) + keyboard + mouse
    s.box(mat("Laptop_Body", "#9EA2A6", 0.35, metal=0.8), L * 0.72, L * 0.72 + 0.30, 0.30, 0.51, T, T + 0.016, bevel=0.003)
    s.box(M["dark"], mx - 0.22, mx + 0.22, 0.38, 0.52, T, T + 0.018, bevel=0.004)
    s.box(M["dark"], mx + 0.30, mx + 0.36, 0.42, 0.52, T, T + 0.02, bevel=0.01)
    # desk phone, mug, notebook + pen, walkie-talkie
    s.box(M["black"], 0.08, 0.28, 0.20, 0.38, T, T + 0.05, bevel=0.008)
    s.cyl(mat("Mug_Red", "#E03A3F", 0.3, coat=0.4), (L * 0.70, 0.60, T), (L * 0.70, 0.60, T + 0.095), 0.042, seg=28)
    s.box(mat("Notebook_Black", "#202022", 0.6), L * 0.50, L * 0.50 + 0.15, 0.48, 0.69, T, T + 0.012)
    s.cyl(M["chrome"], (L * 0.50 + 0.17, 0.50, T + 0.005), (L * 0.50 + 0.17, 0.66, T + 0.005), 0.004, seg=8)
    # small "On call" tent card on the ledge, facing the door
    card = mat("OnCall_Card", "#009967", 0.5)
    lz, ly = LEDGE_H + 0.025, -0.05 - LEDGE_D / 2 + 0.02
    s.box(card, L * 0.30, L * 0.30 + 0.16, ly - 0.03, ly - 0.025, lz, lz + 0.09)
    s.box(M["white"], L * 0.30 + 0.02, L * 0.30 + 0.14, ly - 0.0305, ly - 0.03, lz + 0.03, lz + 0.06)
    # sign-in tablet on the ledge (for visitors), pen pot
    s.box(M["black"], L * 0.62, L * 0.62 + 0.25, ly - 0.08, ly + 0.08, lz, lz + 0.008, bevel=0.004)
    s.box(M["lcd"], L * 0.62 + 0.01, L * 0.62 + 0.24, ly - 0.07, ly + 0.07, lz + 0.008, lz + 0.0085)
    s.cyl(MAT["bins"][1], (L * 0.90, ly, lz), (L * 0.90, ly, lz + 0.10), 0.035, seg=20)
    s.emit("OnCall_Desk_Props", col, loc, rot)
    # chair (sitter with the spine behind, facing the door = +x)
    c = at(L * 0.50, D + 0.30, 0.0)
    r = math.pi / 2 - math.radians(6)
    off = Matrix.Rotation(r, 4, "Z") @ Vector((-0.22, -0.22, 0))
    tex["chair"]().emit("OnCall_Chair", col, Vector((c.x, c.y, 0)) + off, r)


def build():
    col = clear_collection("Welcome")
    tv_wall(col)
    oncall_desk(col)
    print("welcome: Fab Lab TV on the spine + on-call desk facing the door")


build()
