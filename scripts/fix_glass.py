"""Thin architectural glass for every single-plane pane (material Glass_Clear). Re-runnable.

The panes (façade, CNC-room and laser-room glazing, glass doors) are zero-thickness planes. A refractive
Principled BSDF (IOR 1.5) bends rays on entry and never bends them back, so everything seen through the
glass is shifted and warped. Real window glass is two parallel faces whose refractions cancel, so model it
as: straight-through transmission (faint green edge tint) mixed with a sharp Fresnel reflection, and fully
transparent to shadow rays so the sun still reaches the floor.
"""
import bpy

TINT = (0.955, 0.975, 0.965, 1.0)      # slight float-glass green
IOR = 1.52


def build():
    m = bpy.data.materials.get("Glass_Clear") or bpy.data.materials.new("Glass_Clear")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    lp = nt.nodes.new("ShaderNodeLightPath")
    fres = nt.nodes.new("ShaderNodeFresnel")
    # Fresnel inverts the IOR on back faces (ray leaving glass -> total internal reflection past ~42 deg,
    # a mirror arc on the pane). A thin pane reflects the same from both sides: feed 1/IOR on back faces.
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ior = nt.nodes.new("ShaderNodeMath")
    ior.operation = "MULTIPLY_ADD"
    ior.inputs[1].default_value = 1 / IOR - IOR
    ior.inputs[2].default_value = IOR
    nt.links.new(geo.outputs["Backfacing"], ior.inputs[0])
    nt.links.new(ior.outputs["Value"], fres.inputs["IOR"])
    geo.location, ior.location = (-1100, 200), (-900, 200)
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    clear.inputs["Color"].default_value = TINT
    gloss = nt.nodes.new("ShaderNodeBsdfGlossy")
    gloss.inputs["Roughness"].default_value = 0.0
    glass = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fres.outputs["Fac"], glass.inputs["Fac"])
    nt.links.new(clear.outputs["BSDF"], glass.inputs[1])
    nt.links.new(gloss.outputs["BSDF"], glass.inputs[2])
    shadow = nt.nodes.new("ShaderNodeBsdfTransparent")
    final = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], final.inputs["Fac"])
    nt.links.new(glass.outputs["Shader"], final.inputs[1])
    nt.links.new(shadow.outputs["BSDF"], final.inputs[2])
    nt.links.new(final.outputs["Shader"], out.inputs["Surface"])
    for i, n in enumerate((lp, fres, clear, gloss, glass, shadow, final, out)):
        n.location = (i * 200 - 700, 0)
    m.diffuse_color = (0.8, 0.9, 0.9, 0.25)
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"                            # EEVEE/viewport: see through
    users = [o.name for o in bpy.data.objects if o.type == "MESH" and m.name in [x.name for x in o.data.materials if x]]
    print("Glass_Clear -> thin glass on %d objects" % len(users))


build()
