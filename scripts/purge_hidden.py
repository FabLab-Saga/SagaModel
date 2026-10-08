"""Delete every render-hidden object (the colleague's SketchUp leftovers that builders used to hide) from the file.

Kept, even though hidden:
- KEEP: per-camera ground (render_cams/render_finals toggle these on for some shots),
- anything a visible object still depends on (boolean cutters, parents, curve bevels, constraint targets,
  collection-instance sources), found at run time.
Mesh/curve data, materials and images that only the deleted objects used are removed too; datablocks that were
already orphaned before the run are left alone. Colleague collections left empty are unlinked.
Re-runnable: a second run finds nothing to delete.
"""
import bpy

KEEP = {"Ground_Grass", "Ground_Paving", "Ceiling_SlabRing", "Ceiling_Slab"}
COLLEAGUE_COLS = ("Untagged", "Кухня", "мебели")


def script_literals():
    import glob
    import os
    import re
    out = set()
    for f in glob.glob(os.path.join(bpy.path.abspath("//scripts"), "*.py")):
        out |= set(re.findall(r"[\"']([^\"'\n]+)[\"']", open(f, encoding="utf-8").read()))
    return out


def needed_by_visible(hidden):
    need = set()
    for o in bpy.data.objects:
        if o.hide_render:
            continue
        p = o.parent
        while p:
            need.add(p)
            p = p.parent
        for m in o.modifiers:
            for a in ("object", "target", "mirror_object", "offset_object", "start_cap", "end_cap", "curve",
                      "auxiliary_target"):
                t = getattr(m, a, None)
                if isinstance(t, bpy.types.Object):
                    need.add(t)
        for c in o.constraints:
            if getattr(c, "target", None):
                need.add(c.target)
        if o.type == "CURVE":
            need.update(t for t in (o.data.bevel_object, o.data.taper_object) if t)
        if o.instance_type == "COLLECTION" and o.instance_collection:
            need.update(o.instance_collection.all_objects)
    return need & hidden


def purge():
    named = script_literals()               # builders look datablocks up by name (meshes["Profile_2020"],
    hidden = {o for o in bpy.data.objects if o.hide_render and o.name not in KEEP}   # materials["Sofa_LightGrey"])
    hidden -= needed_by_visible(hidden)
    for n in ("Profile_2020", "Profile_4040"):                     # profile templates for profile_furniture.Part
        if n in bpy.data.meshes:
            bpy.data.meshes[n].use_fake_user = True
    data = {o.data for o in hidden if o.data is not None and o.data.name not in named}
    mats = {s.material for o in hidden for s in o.material_slots if s.material}
    mats |= {m for d in data if hasattr(d, "materials") for m in d.materials if m}
    n_obj = len(hidden)
    bpy.data.batch_remove(hidden)
    gone_data = [d for d in data if d.users == 0]
    imgs = {n.image for m in mats if m.use_nodes and m.node_tree for n in m.node_tree.nodes
            if n.type == "TEX_IMAGE" and n.image}
    bpy.data.batch_remove(gone_data)
    gone_mats = [m for m in mats if m.users == 0 and m.name not in named]
    bpy.data.batch_remove(gone_mats)
    gone_imgs = [i for i in imgs if i.users == 0 and i.name not in named]
    bpy.data.batch_remove(gone_imgs)
    gone_cols = []
    for name in COLLEAGUE_COLS:
        c = bpy.data.collections.get(name)
        if c and not c.all_objects and not c.children:
            gone_cols.append(name)
            bpy.data.collections.remove(c)
    print("purge_hidden: %d objects, %d mesh/curve data, %d materials, %d images, collections %s"
          % (n_obj, len(gone_data), len(gone_mats), len(gone_imgs), gone_cols))


purge()
