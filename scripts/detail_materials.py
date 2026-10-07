"""Close-up surface detail for machine materials (re-runnable; node trees rebuilt by name).
- Mach_PrusaOrange: printed PETG - 0.2 mm layer lines (bump along world Z), satin sheen.
- Mach_PEI: textured powder-coated sheet - fine speckle + micro bump.
- Mach_AluFrame: black anodised, brushed (anisotropic-ish roughness streaks).
"""
import bpy


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c) + (1,)


def fresh(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    nt = m.node_tree
    return m, nt, nt.nodes.new, nt.links.new


def printed(name, hexcol):
    m, nt, N, L = fresh(name)
    out, b, geo = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled"), N("ShaderNodeNewGeometry")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = 0.42
    b.inputs["Coat Weight"].default_value = 0.15
    sep = N("ShaderNodeSeparateXYZ"); L(geo.outputs["Position"], sep.inputs["Vector"])
    mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 3.14159 * 2 / 0.0002
    L(sep.outputs["Z"], mul.inputs[0])
    sn = N("ShaderNodeMath"); sn.operation = "SINE"; L(mul.outputs[0], sn.inputs[0])
    bump = N("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25; bump.inputs["Distance"].default_value = 0.00005
    L(sn.outputs[0], bump.inputs["Height"])
    bv = N("ShaderNodeBevel"); bv.inputs["Radius"].default_value = 0.0015; L(bump.outputs["Normal"], bv.inputs["Normal"])
    L(bv.outputs["Normal"], b.inputs["Normal"]); L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = lin(hexcol)


def pei(name):
    m, nt, N, L = fresh(name)
    out, b, geo = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled"), N("ShaderNodeNewGeometry")
    nz = N("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2500; nz.inputs["Detail"].default_value = 4
    L(geo.outputs["Position"], nz.inputs["Vector"])
    ramp = N("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = lin("#151413"); ramp.color_ramp.elements[1].color = lin("#3A3633")
    L(nz.outputs["Fac"], ramp.inputs["Fac"]); L(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.7
    bump = N("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.6; bump.inputs["Distance"].default_value = 0.0002
    L(nz.outputs["Fac"], bump.inputs["Height"]); L(bump.outputs["Normal"], b.inputs["Normal"])
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = lin("#222020")


def brushed_black(name):
    m, nt, N, L = fresh(name)
    out, b, geo = N("ShaderNodeOutputMaterial"), N("ShaderNodeBsdfPrincipled"), N("ShaderNodeNewGeometry")
    b.inputs["Base Color"].default_value = lin("#141414")
    b.inputs["Metallic"].default_value = 0.85
    mp = N("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (2.0, 2.0, 900.0)
    L(geo.outputs["Position"], mp.inputs["Vector"])
    nz = N("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3; nz.inputs["Detail"].default_value = 8
    L(mp.outputs["Vector"], nz.inputs["Vector"])
    rr = N("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.28; rr.inputs["To Max"].default_value = 0.45
    L(nz.outputs["Fac"], rr.inputs["Value"]); L(rr.outputs["Result"], b.inputs["Roughness"])
    bv = N("ShaderNodeBevel"); bv.inputs["Radius"].default_value = 0.001; L(bv.outputs["Normal"], b.inputs["Normal"])
    L(b.outputs["BSDF"], out.inputs["Surface"])
    m.diffuse_color = lin("#141414")


printed("Mach_PrusaOrange", "#FA6831")
pei("Mach_PEI")
brushed_black("Mach_AluFrame")
print("detail materials done")
