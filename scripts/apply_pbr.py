"""Photoreal pass 1: scanned PBR materials (Poly Haven CC0), render-time bevels, smooth columns.

Materials keep their names (so every object assignment stays), only their node trees are
rebuilt. Textures are box-projected in world space at the scan's real-world size, so no UVs
are needed. Brand-colour materials (felt, mural, signs, bins) are left untouched.
Run inside Blender: exec(open(path).read()).
"""
import json
import math

import bpy

PH = bpy.path.abspath("//assets/polyhaven/")


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def size_m(asset):
    d = json.load(open(PH + asset + "/info.json")).get("dimensions_mm") or [2000, 2000]
    return max(d[0], d[1]) / 1000.0


def img(asset, mapname, noncolor):
    path = PH + f"{asset}/{mapname}.jpg"
    im = next((i for i in bpy.data.images if bpy.path.abspath(i.filepath) == path), None) or bpy.data.images.load(path)
    im.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    return im


def pbr(mat_name, asset, rot_z=0.0, scale=1.0, tint=None, tint_mix=0.0, rough_mul=1.0, normal=1.0, bevel=0.004,
        blend=0.2, coat=0.0):
    m = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    b = N("ShaderNodeBsdfPrincipled")
    geo = N("ShaderNodeNewGeometry")
    mp = N("ShaderNodeMapping")
    s = 1.0 / (size_m(asset) * scale)
    mp.inputs["Scale"].default_value = (s, s, s)
    mp.inputs["Rotation"].default_value = (0, 0, rot_z)
    L(geo.outputs["Position"], mp.inputs["Vector"])

    # world-space triplanar: three planar lookups blended by the WORLD normal, so rotated and
    # non-uniformly scaled objects (SketchUp instances) get undistorted textures at true scale
    sep = N("ShaderNodeSeparateXYZ")
    L(mp.outputs["Vector"], sep.inputs["Vector"])
    planes = []
    for a, bb in (("Y", "Z"), ("X", "Z"), ("X", "Y")):
        cmb = N("ShaderNodeCombineXYZ")
        L(sep.outputs[a], cmb.inputs["X"])
        L(sep.outputs[bb], cmb.inputs["Y"])
        planes.append(cmb)
    nabs = N("ShaderNodeVectorMath")
    nabs.operation = "ABSOLUTE"
    L(geo.outputs["Normal"], nabs.inputs[0])
    nsep = N("ShaderNodeSeparateXYZ")
    L(nabs.outputs["Vector"], nsep.inputs["Vector"])
    w = []
    for comp in ("X", "Y", "Z"):                                     # sharpen the blend: |n|^6
        pw = N("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 6.0
        L(nsep.outputs[comp], pw.inputs[0])
        w.append(pw)
    tot = N("ShaderNodeMath")
    L(w[0].outputs[0], tot.inputs[0])
    L(w[1].outputs[0], tot.inputs[1])
    tot2 = N("ShaderNodeMath")
    L(tot.outputs[0], tot2.inputs[0])
    L(w[2].outputs[0], tot2.inputs[1])
    weights = []
    for pw in w:
        dv = N("ShaderNodeMath")
        dv.operation = "DIVIDE"
        L(pw.outputs[0], dv.inputs[0])
        L(tot2.outputs[0], dv.inputs[1])
        weights.append(dv)

    class _Out:                                                       # mimic an image node's .outputs["Color"]
        def __init__(self, sock):
            self.outputs = {"Color": sock}

    def tex(mapname, noncolor):
        acc = None
        for plane, wt in zip(planes, weights):
            t = N("ShaderNodeTexImage")
            t.image = img(asset, mapname, noncolor)
            L(plane.outputs["Vector"], t.inputs["Vector"])
            sc = N("ShaderNodeVectorMath")
            sc.operation = "SCALE"
            L(t.outputs["Color"], sc.inputs[0])
            L(wt.outputs[0], sc.inputs["Scale"])
            if acc is None:
                acc = sc.outputs["Vector"]
            else:
                ad = N("ShaderNodeVectorMath")
                L(acc, ad.inputs[0])
                L(sc.outputs["Vector"], ad.inputs[1])
                acc = ad.outputs["Vector"]
        return _Out(acc)

    diff = tex("diff", False)
    col = diff.outputs["Color"]
    if tint:
        mix = N("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.inputs["Factor"].default_value = tint_mix
        L(col, mix.inputs["A"])
        mix.inputs["B"].default_value = lin(tint)
        col = mix.outputs["Result"]
    L(col, b.inputs["Base Color"])
    rough = tex("rough", True)
    if rough_mul != 1.0:
        mm = N("ShaderNodeMath")
        mm.operation = "MULTIPLY"
        mm.inputs[1].default_value = rough_mul
        L(rough.outputs["Color"], mm.inputs[0])
        L(mm.outputs["Value"], b.inputs["Roughness"])
    else:
        L(rough.outputs["Color"], b.inputs["Roughness"])
    nrm = N("ShaderNodeBump")                                         # relief from the scan's displacement map
    nrm.inputs["Strength"].default_value = 0.6 * normal
    nrm.inputs["Distance"].default_value = 0.002
    dsum = tex("disp", True).outputs["Color"]
    dsep = N("ShaderNodeSeparateXYZ")
    L(dsum, dsep.inputs["Vector"])
    L(dsep.outputs["X"], nrm.inputs["Height"])
    if bevel:
        bv = N("ShaderNodeBevel")
        bv.samples = 6
        bv.inputs["Radius"].default_value = bevel
        L(nrm.outputs["Normal"], bv.inputs["Normal"])
        L(bv.outputs["Normal"], b.inputs["Normal"])
    else:
        L(nrm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = lin(tint) if tint else (0.6, 0.5, 0.4, 1)
    return m


def add_bevel(mat_name, radius=0.002):
    """Render-time rounded edges on an existing (non-PBR) material."""
    m = bpy.data.materials.get(mat_name)
    if not m or not m.use_nodes:
        return
    nt = m.node_tree
    b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if not b or any(n.type == "BEVEL" for n in nt.nodes):
        return
    bv = nt.nodes.new("ShaderNodeBevel")
    bv.samples = 6
    bv.inputs["Radius"].default_value = radius
    old = next((l for l in nt.links if l.to_socket == b.inputs["Normal"]), None)
    if old:
        nt.links.new(old.from_socket, bv.inputs["Normal"])
        nt.links.remove(old)
    nt.links.new(bv.outputs["Normal"], b.inputs["Normal"])


def run():
    pbr("Parquet", "wood_floor_worn", rot_z=math.radians(90), coat=0.0, rough_mul=1.35, bevel=0)
    pbr("Concrete_Exposed", "concrete_slab_wall", normal=0.8)
    pbr("Paint_White", "painted_plaster_wall", tint="#EEECE7", tint_mix=0.82, normal=0.35, rough_mul=1.0)
    pbr("OSB", "oriented_strand_board", normal=0.8)                 # no rotation: box projection on vertical boards
    for mname in ("Plywood_Birch", "Material_27"):
        pbr(mname, "plywood", normal=0.6, coat=0.0, bevel=0.0015, rough_mul=2.2)
    pbr("Sofa_LightGrey", "rough_linen", scale=0.6, tint="#9C9B96", tint_mix=0.6, normal=1.6, bevel=0.02)
    for mname in ("Alu_Black_Anodized", "Alu_Frame_Dark", "Mach_White", "Mach_Grey", "Mach_DarkGrey", "Mach_Black",
                  "Desk_Black", "Cart_Black", "Galvanised", "Enamel_Black"):
        add_bevel(mname, 0.0015)
    # smooth the SketchUp columns (shade smooth by angle on the shell and the column claddings)
    for name in ("ROOT.geo0", "Component_286302.geo0"):
        o = bpy.data.objects.get(name)
        if o is None:
            continue
        for p in o.data.polygons:
            p.use_smooth = True
        o.data.set_sharp_from_angle(angle=math.radians(35))
    print("pbr pass done")


run()


def fix_columns_and_sofas():
    """Replace the coarse SketchUp column claddings with true cylinders; soften the sofas."""
    from mathutils import Vector
    import bmesh
    col = bpy.data.collections.get("Shell")
    for src in ("Component_286302",):
        o = bpy.data.objects.get(src)
        if not o:
            continue
        pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" for c in k.bound_box]
        cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
        cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
        r = (max(p.x for p in pts) - min(p.x for p in pts)) / 2
        z1 = max(p.z for p in pts)
        name = src + "_Smooth"
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.meshes.remove(old.data)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=r, radius2=r, depth=z1,
                              matrix=__import__("mathutils").Matrix.Translation((cx, cy, z1 / 2)))
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(bpy.data.materials["Paint_White"])
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = True
        print("column replaced:", src, "r=%.3f" % r)
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("Sofa_") and o.name.endswith("_Sofa_LightGrey"):
            if "Soft" not in o.modifiers:
                bv = o.modifiers.new("Soft", "BEVEL")
                bv.width = 0.035
                bv.segments = 4
                bv.limit_method = "ANGLE"
                sd = o.modifiers.new("Subd", "SUBSURF")
                sd.levels = 1
                sd.render_levels = 2
            for p in o.data.polygons:
                p.use_smooth = True


fix_columns_and_sofas()
