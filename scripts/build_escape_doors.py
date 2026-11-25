"""Escape door pair (ÚT) in the SSW façade by the lounge. Re-runnable ("EscapeDoors" collection + boolean cutters on
the façade glass/frames). Run after build_entrance_bay; before build_signs/apply_pbr is fine (own materials).

Facts: the Andrúm AT 20-10-02 ground-floor plan shows a pair of escape doors "ÚT" in the SSW glazing at
y ~32.4-34.3; Magnús (2026-11-25): "Yes, it's real: model it", look = "Glass leaves in the same dark façade frames,
panic bars, small green exit pictogram above". The conversation pit stays in front of it (Magnús, 2026-11-25).
My choices: the pair fills the façade bay between the existing mullions at y 32.69-32.74 and 34.18-34.20 (the
drawing's 1.9 m is approximate; the bay is 1.44 m clear), so two 0.72 m leaves, outward opening (escape), hinged
on the mullions, meeting stiles in the middle; door head with a transom at 2.40 m, the façade glass stays above;
70 mm stiles, deeper bottom rail, stainless panic bars inside, no outside handle, flat threshold; pictogram sign
(scripts/make_exit_sign.py, my own drawing) hung under the soffit inside, above the door.
"""
import bmesh
import bpy
from mathutils import Vector

HERE = bpy.path.abspath("//scripts/")
_s = open(HERE + "build_staff_area.py").read()
sa = {}
exec(_s[:_s.index("\ndef build():")], sa)
Part, mat = sa["Part"], sa["mat"]

XC = 32.53                       # façade frame centre plane (frames x 32.47-32.59, glass 32.525-32.535)
Y0, Y1 = 32.74, 34.18            # clear opening between the existing mullions
H, F = 2.40, 0.06                # leaf head, transom depth
MID = (Y0 + Y1) / 2


def clear_collection(name):
    return sa["clear_collection"](name)


def cutter(target, name, x0, x1, y0, y1, z0, z1):
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
    t = bpy.data.objects[target]
    mod = t.modifiers.get(name) or t.modifiers.new(name, "BOOLEAN")
    mod.operation, mod.solver, mod.object = "DIFFERENCE", "EXACT", ob


def sign_material():
    m = bpy.data.materials.get("Sign_Exit") or bpy.data.materials.new("Sign_Exit")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    img = bpy.data.images.load(bpy.path.abspath("//assets/signs/exit_pictogram.png"), check_existing=True)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image, tex.interpolation = img, "Cubic"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.35
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex.outputs["Color"], b.inputs["Emission Color"])      # internally lit sign, faint
    b.inputs["Emission Strength"].default_value = 0.6
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    return m


def exit_sign(col):
    """0.40 x 0.20 pictogram box hung on two rods from the soffit, face towards the room (-x)."""
    fr = bpy.data.materials["Alu_Frame_Dark"]
    w, h, t = 0.40, 0.20, 0.035
    xs, z0 = XC - 0.25, 2.62
    p = Part()
    p.box(fr, xs - t, xs, MID - w / 2 - 0.008, MID + w / 2 + 0.008, z0 - 0.008, z0 + h + 0.008, bevel=0.003)
    for dy in (-0.15, 0.15):
        p.cyl(fr, (xs - t / 2, MID + dy, z0 + h), (xs - t / 2, MID + dy, sa["SOFFIT"]), 0.004, seg=8)
    p.emit("Exit_Sign_Box", col, Vector((0, 0, 0)))
    me = bpy.data.meshes.new("Exit_Sign_Face")
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    xf = xs - t - 0.0005
    pts = [(xf, MID + w / 2, z0), (xf, MID - w / 2, z0), (xf, MID - w / 2, z0 + h), (xf, MID + w / 2, z0 + h)]
    f = bm.faces.new([bm.verts.new(q) for q in pts])               # normal -x (towards the room)
    for loop, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = c
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(sign_material())
    o = bpy.data.objects.new("Exit_Sign_Face", me)
    col.objects.link(o)


def doors(col):
    fr, gl = bpy.data.materials["Alu_Frame_Dark"], bpy.data.materials["Glass_Clear"]
    steel = mat("Steel_Brushed_PanicBar", "#C9CCCF", 0.28, metal=1.0)
    p, g = Part(), Part()
    p.box(fr, XC - 0.06, XC + 0.06, Y0, Y1, H, H + F)                    # transom (door head)
    p.box(mat("Threshold_Alu", "#5A5D60", 0.4, metal=0.8), XC - 0.07, XC + 0.07, Y0, Y1, 0.0, 0.008)
    for (a, b, hinge) in ((Y0, MID, Y0), (MID, Y1, Y1)):              # closed leaves
        a, b = a + 0.003, b - 0.003
        for ya, yb in ((a, a + 0.07), (b - 0.07, b)):                 # stiles
            p.box(fr, XC - 0.03, XC + 0.03, ya, yb, 0.008, H - 0.003)
        p.box(fr, XC - 0.03, XC + 0.03, a, b, 0.008, 0.20)              # bottom rail
        p.box(fr, XC - 0.03, XC + 0.03, a, b, H - 0.08, H - 0.003)      # top rail
        g.box(gl, XC - 0.0005, XC + 0.0005, a + 0.07, b - 0.07, 0.20, H - 0.08)
        xi = XC - 0.03                                                # panic bar on the inside face
        for yy in (a + 0.09, b - 0.09):
            p.box(steel, xi - 0.075, xi, yy - 0.02, yy + 0.02, 0.98, 1.06, bevel=0.006)
        p.cyl(steel, (xi - 0.065, a + 0.09, 1.02), (xi - 0.065, b - 0.09, 1.02), 0.017, seg=16)
        for z in (0.30, 1.20, 2.10):                                  # hinges on the outside face (out-swing)
            yh = hinge + (0.004 if hinge == Y0 else -0.004)
            p.cyl(steel, (XC + 0.045, yh, z), (XC + 0.045, yh, z + 0.10), 0.010, seg=12)
    p.box(fr, XC - 0.032, XC + 0.032, MID - 0.004, MID + 0.004, 0.008, H - 0.003)   # astragal
    p.emit("Escape_Doors_Frame", col, Vector((0, 0, 0)))
    g.emit("Escape_Doors_Glass", col, Vector((0, 0, 0)))


def build():
    col = clear_collection("EscapeDoors")
    cutter("Facade_SSW_Glass", "Cut_Escape_Glass", 32.40, 32.66, Y0, Y1, -0.05, H + F - 0.005)
    cutter("Facade_SSW_Frames", "Cut_Escape_Sill", 32.40, 32.66, Y0 + 0.001, Y1 - 0.001, -0.05, 0.065)
    doors(col)
    exit_sign(col)
    print("escape doors: pair %.2f m (2 x %.2f) in the SSW façade, y %.2f-%.2f, head %.2f" % (Y1 - Y0, (Y1 - Y0) / 2, Y0, Y1, H))


build()
