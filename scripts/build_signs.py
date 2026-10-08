"""Equipment signs from the Fab Lab Ísland brand manual (refs/branding/signage), placed by
their machines. Re-runnable: rebuilds the "Signs" collection.

The manual's signs are 25 x 25 cm; SIZE is larger so they read in renders.
Mounted signs sit flat on a surface; hung signs are double-sided on two cables.
Model frame: +X = SSW, +Y = ESE; facing = direction the sign face points.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

SIZE = 0.40
SOFFIT = 3.93
IMG = "//assets/signs/{}.png"
FACE = {"-x": -math.pi / 2, "+x": math.pi / 2, "-y": 0.0, "+y": math.pi}

# name, image, centre (x, y, z), facing, hung?
SIGNS = [
    ("Sign_3DPrentari", "3d_prentari", (28.76, 23.63, 2.42 + 0.20), "-x", False),     # on the print-farm top frame
    ("Sign_Laserskeri", "laser", (29.30, 26.34, 2.60), "-x", True),                   # hung at the laser-room door
    ("Sign_Fraesivel", "fraesi_vel", (21.40, 21.836, 2.48), "+y", False),              # above the CNC-room door
    ("Sign_Rafeinda", "rafeinda", (24.11, 29.96, 1.92), "+y", False),                 # microelectronics tool wall
    ("Sign_Verkfaeri", "verkfaeri", (20.95, 24.25, 1.93), "+x", True),                # hand-tool wall on the NNE glass
    ("Sign_Vinylskeri", "vinylskeri", (21.30, 27.75, 2.45), "+x", True),              # over the vinyl stands + cutter counter
    ("Sign_Saumavel", "saumavel", (31.05, 27.30, 2.45), "+y", True),                  # over the sewing bench (textile)
]


def sign_material(key):
    name = f"Sign_{key}"
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    img = bpy.data.images.get(f"{key}.png") or bpy.data.images.load(IMG.format(key))
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Cubic"
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Roughness"].default_value = 0.55                     # printed dibond, satin
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = (0.8, 0.8, 0.8, 1)
    return m


def edge_material():
    m = bpy.data.materials.get("Sign_Edge") or bpy.data.materials.new("Sign_Edge")
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.02, 0.02, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.4
    return m


def face(bm, uv, s, y, flip):
    """Square face in local XZ at depth y, normal -y (flip: +y with mirrored UVs so it reads correctly)."""
    h = s / 2
    pts = [(-h, y, -h), (h, y, -h), (h, y, h), (-h, y, h)]
    if flip:
        pts = pts[::-1]
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    for loop in f.loops:
        u = (loop.vert.co.x + h) / s
        loop[uv].uv = ((1 - u) if flip else u, (loop.vert.co.z + h) / s)
    return f


def build():
    scene = bpy.context.scene
    col = bpy.data.collections.get("Signs") or bpy.data.collections.new("Signs")
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    edge = edge_material()
    t = 0.006                                                      # 6 mm dibond panel
    for name, key, (x, y, z), facing, hung in SIGNS:
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        front = face(bm, uv, SIZE, -t / 2, False)
        back = face(bm, uv, SIZE, t / 2, True)
        front.material_index = 0
        back.material_index = 0 if hung else 1
        h = SIZE / 2                                               # panel edges
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co = Vector((h * 1.0005 if v.co.x > 0 else -h * 1.0005, t / 2 * 0.98 if v.co.y > 0 else -t / 2 * 0.98,
                           h * 1.0005 if v.co.z > 0 else -h * 1.0005))
        for f in {f for v in r["verts"] for f in v.link_faces}:
            f.material_index = 1
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(sign_material(key))
        me.materials.append(edge)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        ob.matrix_world = Matrix.Translation((x, y, z)) @ Matrix.Rotation(FACE[facing], 4, "Z")
        if hung:                                                   # two cables to the slab
            cb = bmesh.new()
            for dx in (-h * 0.8, h * 0.8):
                a = ob.matrix_world @ Vector((dx, 0, h))
                b = Vector((a.x, a.y, SOFFIT))
                d = b - a
                bmesh.ops.create_cone(cb, cap_ends=False, segments=6, radius1=0.0015, radius2=0.0015, depth=d.length,
                                      matrix=Matrix.Translation((a + b) / 2))
            cme = bpy.data.meshes.new(name + "_Cables")
            cb.to_mesh(cme)
            cb.free()
            cme.materials.append(edge)
            col.objects.link(bpy.data.objects.new(name + "_Cables", cme))
    return len(SIGNS)


print("signs placed:", build())
