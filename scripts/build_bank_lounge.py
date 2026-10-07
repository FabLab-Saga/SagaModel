"""Búnaðarbankinn (equipment bank) and the lounge/entryway. Re-runnable.

Equipment bank = the enclosure at the ESE end (model frame: +X = SSW, +Y = ESE):
  Boxes only - no machinery in the bank (user, 2026-10-07).
  A  back-wall run, y 37.73-38.33, 60 cm deep, x 21.05 -> ~32.4: large-box bays.
  B  OSB-wall run, y 35.22-35.62, 40 cm deep: small boxes, full height.
  C  NNE end, x 21.05-21.65, 60 cm deep: biggest boxes.
  Contents: IKEA SAMLA-style clear boxes (5-130 L) full of random teaching kit.
Lounge/entryway along the SSW glass (y 27.05-34.55; main entrance at y 35.1 kept clear):
  two conversation groups with the list's Cleveland sofas, profile coffee tables,
  Flöff-felt poufs, TV on wheels.
Placeholders inside these areas are hidden, not deleted.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = bpy.path.abspath("//scripts/")
lib = {}
exec(open(HERE + "profile_furniture.py").read(), lib)
MAT = lib["materials"]()
_src = open(HERE + "build_machines.py").read()
mach = {}
exec(_src[:_src.index("def build():")], mach)          # machine models only, no build
mach["materials"]()
M = mach["M"]
Part = lib["Part"]
mat = lib["simple_mat"]
lin = lib["lin"]
rng = random.Random(7)


# ---------------------------------------------------------------- materials
def clear_plastic(name, tint, opacity):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    gl = nt.nodes.new("ShaderNodeBsdfPrincipled")
    gl.inputs["Base Color"].default_value = lin(tint)
    gl.inputs["Roughness"].default_value = 0.18
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (0.93, 0.95, 0.97, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 1.0 - opacity
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(gl.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*lin(tint)[:3], 0.3)
    m.surface_render_method = "BLENDED"
    return m


def fabric(name, hexcol):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = lin(hexcol)
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Sheen Weight"].default_value = 0.7
    if not any(n.type == "TEX_NOISE" for n in nt.nodes):
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = 700
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.15
        nt.links.new(geo.outputs["Position"], nz.inputs["Vector"])
        nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = lin(hexcol)
    return m


SAMLA = clear_plastic("SAMLA_Clear", "#DDE6EA", 0.32)
LID = clear_plastic("SAMLA_Lid", "#CFE0EA", 0.45)
WHITE_BOX = mat("Box_White", "#F1F0EC", 0.4)
LABEL = mat("Label_Paper", "#FAFAF7", 0.7)
STEEL = mat("Cart_Black", "#1F1F20", 0.45, metal=0.3)
SOFA = fabric("Sofa_LightGrey", "#C2C2BD")
RUG = fabric("Rug_Grey", "#8D8B86")
SCREEN = mat("TV_Screen", "#0B0C0E", 0.08, coat=0.8)
STUFF = MAT["bins"] + [mat("Stuff_White", "#EDEDEA", 0.4), mat("Stuff_Black", "#1A1A1A", 0.35),
                       mat("Stuff_Grey", "#7C8085", 0.4), mat("Stuff_Teal", "#2FA4A0", 0.4)]

# SAMLA sizes (w, d, h), litres as name
SIZES = {5: (0.28, 0.20, 0.14), 11: (0.39, 0.28, 0.14), 22: (0.39, 0.28, 0.28),
         45: (0.57, 0.39, 0.28), 65: (0.57, 0.39, 0.42), 130: (0.79, 0.57, 0.43)}


# ---------------------------------------------------------------- boxes
def samla(part, x, y, z, size, white=False):
    """Box with lid and label in the part's local frame; front face at y."""
    w, d, h = SIZES[size]
    body = WHITE_BOX if white else SAMLA
    t = 0.004
    part.box(body, x, x + w, y, y + d, z, z + t)                        # floor
    part.box(body, x, x + w, y, y + t, z, z + h - 0.02)                 # front
    part.box(body, x, x + w, y + d - t, y + d, z, z + h - 0.02)
    part.box(body, x, x + t, y, y + d, z, z + h - 0.02)
    part.box(body, x + w - t, x + w, y, y + d, z, z + h - 0.02)
    part.box(LID, x - 0.006, x + w + 0.006, y - 0.006, y + d + 0.006, z + h - 0.02, z + h, bevel=0.004)
    part.box(LABEL, x + w * 0.3, x + w * 0.7, y - 0.002, y, z + h * 0.45, z + h * 0.62)
    if not white:                                                        # random kit inside
        fill = rng.uniform(0.45, 0.85) * (h - 0.03)
        cx = x + 0.015
        while cx < x + w - 0.05:
            cw = rng.uniform(0.04, min(0.18, x + w - 0.015 - cx))
            for row in range(2):
                ch = fill * rng.uniform(0.5, 1.0)
                cy0 = y + 0.015 + row * (d - 0.03) / 2
                part.box(rng.choice(STUFF), cx, cx + cw * 0.92, cy0, cy0 + (d - 0.03) / 2 * 0.9, z + t, z + t + ch, bevel=0.003)
            cx += cw


def fill_shelf(part, x0, x1, depth, z, clear_h, big=True):
    """Fill one shelf front-to-back with random SAMLA boxes that fit."""
    fits = [s for s, (w, d, h) in SIZES.items() if d <= depth - 0.01 and h <= clear_h - 0.02 and (big or s <= 22)]
    if not fits:
        return
    x = x0 + 0.012
    while True:
        cand = [s for s in fits if x + SIZES[s][0] <= x1 - 0.012]
        if not cand:
            break
        s = rng.choice(cand)
        w, d, h = SIZES[s]
        white = rng.random() < 0.12
        samla(part, x, 0.012, z, s, white)
        if 2 * h + 0.01 <= clear_h - 0.02 and rng.random() < 0.6:     # stack a second box
            on_top = [q for q in cand if SIZES[q][0] <= w and SIZES[q][1] <= d and SIZES[q][2] <= clear_h - 0.03 - h]
            if not on_top:
                x += w + rng.uniform(0.01, 0.04)
                continue
            s2 = rng.choice(on_top)
            samla(part, x + (w - SIZES[s2][0]) / 2, 0.012 + (d - SIZES[s2][1]) / 2, z + h + 0.002, s2, rng.random() < 0.12)
        x += w + rng.uniform(0.01, 0.04)


def fill_unit(slots, levels, height, depth, big=True, skip=()):
    part = Part()
    tops = list(levels) + [height]
    for (bi, li), (xa, xb, _, _, zt) in slots.items():
        if (bi, li) in skip:
            continue
        clear = tops[li + 1] - zt - 0.06                                 # minus next board + its rail
        fill_shelf(part, xa, xb, depth, zt, clear, big)
    return part


# ---------------------------------------------------------------- carts
def bekant(w):
    """IKEA Bekant storage on castors (w x 0.46 x 1.03): black steel mesh carcass, birch drawer."""
    p = Part()
    d, h = 0.46, 1.03
    for x in (0.0, w - 0.02):
        for y in (0.0, d - 0.02):
            p.box(STEEL, x, x + 0.02, y, y + 0.02, 0.07, h)
            p.cyl(MAT["foot"], (x + 0.01, y + 0.01, 0.0), (x + 0.01, y + 0.01, 0.05), 0.025, seg=14)
    for z in (0.07, 0.45, h - 0.02):
        p.box(STEEL, 0, w, 0, d, z, z + 0.02)
    p.box(STEEL, 0, w, d - 0.005, d, 0.07, h)                            # back
    for x in (0.0, w - 0.003):
        p.box(STEEL, x, x + 0.003, 0, d, 0.07, h)                        # sides
    p.box(MAT["ply"], 0.02, w - 0.02, -0.005, d - 0.02, h - 0.24, h - 0.03, bevel=0.003)   # birch drawer
    p.box(STEEL, w * 0.35, w * 0.65, -0.015, -0.005, h - 0.12, h - 0.10)                    # handle
    return p


def bror(w=0.85, d=0.55, h=0.88):
    p = Part()
    for x in (0.0, w - 0.03):
        for y in (0.0, d - 0.03):
            p.box(STEEL, x, x + 0.03, y, y + 0.03, 0.08, h)
            p.cyl(MAT["foot"], (x + 0.015, y + 0.015, 0.0), (x + 0.015, y + 0.015, 0.06), 0.03, seg=14)
    for z in (0.12, h - 0.03):
        p.box(STEEL, 0, w, 0, d, z, z + 0.03, bevel=0.003)
    return p


# ---------------------------------------------------------------- lounge pieces
def sofa(L, d=0.86, h=0.81):
    """Cleveland-style sofa: plinth on short legs, seat + back cushions, square arms."""
    p = Part()
    arm = 0.16
    for x in (0.06, L - 0.10):
        for y in (0.06, d - 0.10):
            p.box(MAT["foot"], x, x + 0.04, y, y + 0.04, 0.0, 0.10)
    p.box(SOFA, 0, L, 0, d, 0.10, 0.30, bevel=0.02)                       # base
    p.box(SOFA, 0, arm, 0, d, 0.10, 0.62, bevel=0.04)                     # arms
    p.box(SOFA, L - arm, L, 0, d, 0.10, 0.62, bevel=0.04)
    p.box(SOFA, arm, L - arm, d - 0.20, d, 0.30, h, bevel=0.05)          # back
    n = 3 if L > 2.0 else 2
    cw = (L - 2 * arm) / n
    for i in range(n):
        x = arm + i * cw
        p.box(SOFA, x + 0.006, x + cw - 0.006, 0.0, d - 0.20, 0.30, 0.44, bevel=0.04)      # seat cushions
        p.box(SOFA, x + 0.01, x + cw - 0.01, d - 0.36, d - 0.18, 0.44, h - 0.03, bevel=0.06)  # back cushions
    return p


def pouf(m, r=0.23, h=0.42):
    p = Part()
    p.cyl(m, (r, r, 0.0), (r, r, h - 0.04), r, seg=40)
    bmesh.ops.create_uvsphere(p.bm(m), u_segments=40, v_segments=10, radius=r,
                              matrix=Matrix.Translation((r, r, h - 0.04)) @ Matrix.Scale(0.18, 4, (0, 0, 1)))
    return p


def tv_stand(sw=1.92, sh=1.10):
    p = Part()
    w, d = 1.10, 0.62
    p.box(STEEL, 0.05, w - 0.05, 0.10, d - 0.10, 0.08, 0.12)                # base
    for x in (0.0, w - 0.06):
        p.box(STEEL, x, x + 0.06, d / 2 - 0.25, d / 2 + 0.25, 0.04, 0.08)   # feet
    p.box(STEEL, w / 2 - 0.05, w / 2 + 0.05, d / 2 - 0.03, d / 2 + 0.03, 0.12, 1.55)  # column
    x0 = w / 2 - sw / 2
    p.box(STEEL, x0, x0 + sw, d / 2 - 0.08, d / 2 - 0.03, 0.80, 0.80 + sh, bevel=0.005)
    p.box(SCREEN, x0 + 0.01, x0 + sw - 0.01, d / 2 - 0.082, d / 2 - 0.08, 0.81, 0.80 + sh - 0.01)
    return p


# ---------------------------------------------------------------- build
def clear_collection(name):
    scene = bpy.context.scene
    col = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    for o in list(col.objects):
        data = o.data
        bpy.data.objects.remove(o)
        if data is not None and data.users == 0:
            (bpy.data.curves if isinstance(data, bpy.types.Curve) else bpy.data.meshes).remove(data)
    return col


def hide_placeholders(x0, x1, y0, y1, keep):
    n = 0
    for o in bpy.data.objects["ROOT"].children:
        if o.name in keep or o.name.startswith(("ROOT", "Saga_Fablab", "glass door", "WINDOW", "osb st2")):
            continue
        pts = [k.matrix_world @ Vector(c) for k in o.children_recursive if k.type == "MESH" for c in k.bound_box]
        if pts and x0 <= min(p.x for p in pts) and max(p.x for p in pts) <= x1 and y0 <= min(p.y for p in pts) and max(p.y for p in pts) <= y1:
            for k in (o, *o.children_recursive):
                k.hide_render = k.hide_viewport = True
            n += 1
    return n


def put(part, name, col, loc, rot, local_xy, z, w, d):
    c = lib["to_world"](loc, rot, (local_xy[0], local_xy[1], 0))
    off = Matrix.Rotation(rot, 4, "Z") @ Vector((-w / 2, -d / 2, 0))
    return part.emit(name, col, Vector((c.x, c.y, z)) + off, rot)


def build():
    bank = clear_collection("EquipmentBank")
    lounge = clear_collection("Lounge")
    hidden = hide_placeholders(20.9, 32.45, 35.15, 38.40, keep=())

    H = 2.42
    # A1: large-box bays at the NNE end of the back wall
    lv_a1 = [0.12, 0.56, 1.00, 1.44, 1.88]
    part, slots, L1 = lib["shelf_unit"]([1.25, 1.25, 1.25], 0.60, H, lv_a1)
    loc, rot = lib["placement"](21.05 + L1 / 2, 38.33 - 0.30, L1, 0.60, "-y")
    part.emit("Bank_A1_Shelving", bank, loc, rot)
    fill_unit(slots, lv_a1, H, 0.60).emit("Bank_A1_Boxes", bank, loc, rot)
    # A2: more box bays along the rest of the back wall (no machinery in the bank - boxes only)
    bays = [1.20] * 6
    lv_a2 = lv_a1
    part, slots2, L2 = lib["shelf_unit"](bays, 0.60, H, lv_a2)
    x2 = 21.05 + L1 + 0.005
    loc2, rot2 = lib["placement"](x2 + L2 / 2, 38.33 - 0.30, L2, 0.60, "-y")
    part.emit("Bank_A2_Shelving", bank, loc2, rot2)
    fill_unit(slots2, lv_a2, H, 0.60).emit("Bank_A2_Boxes", bank, loc2, rot2)
    # B: small boxes against the OSB wall, facing +y
    lv_b = [0.10, 0.48, 0.86, 1.24, 1.62, 2.00]
    part, slots_b, Lb = lib["shelf_unit"]([1.11] * 5, 0.40, H, lv_b)
    loc_b, rot_b = lib["placement"](21.66 + Lb / 2, 35.22 + 0.20, Lb, 0.40, "+y")
    part.emit("Bank_B_SmallBoxShelving", bank, loc_b, rot_b)
    fill_unit(slots_b, lv_b, H, 0.40, big=False).emit("Bank_B_Boxes", bank, loc_b, rot_b)
    # C: NNE end, facing +x: biggest boxes + sewing machines
    lv_c = [0.12, 0.62, 1.12, 1.62, 2.02]
    part, slots_c, Lc = lib["shelf_unit"]([0.95, 0.95], 0.60, H, lv_c)
    loc_c, rot_c = lib["placement"](21.05 + 0.30, 35.66 + Lc / 2, Lc, 0.60, "+x")
    part.emit("Bank_C_Shelving", bank, loc_c, rot_c)
    fill_unit(slots_c, lv_c, H, 0.60).emit("Bank_C_Boxes", bank, loc_c, rot_c)

    # ---------------- lounge / entryway along the SSW glass
    XB = 32.40                                                            # sofa backs against the glass zone
    sofa(2.08).emit("Sofa_Cleveland3_A", lounge, *lib["placement"](XB - 0.43 - 0.05, 28.80, 2.08, 0.86, "-x"))
    sofa(2.08).emit("Sofa_Cleveland3_B", lounge, *lib["placement"](29.10 + 0.43, 28.80, 2.08, 0.86, "+x"))
    part, _ = lib["table_unit"](1.20, 0.60, 0.42, [0.0, 1.16], lower=())
    part.emit("CoffeeTable_1", lounge, *lib["placement"](30.73, 28.80, 1.20, 0.60, "-x"))
    sofa(1.79).emit("Sofa_Cleveland2", lounge, *lib["placement"](XB - 0.43 - 0.05, 32.45, 1.79, 0.86, "-x"))
    part, _ = lib["table_unit"](0.90, 0.55, 0.42, [0.0, 0.86], lower=())
    part.emit("CoffeeTable_2", lounge, *lib["placement"](30.95, 32.45, 0.90, 0.55, "-x"))
    felts = [bpy.data.materials[n] for n in ("Floff_Orange", "Floff_Green", "Floff_Blue")]
    for i, (x, y) in enumerate(((29.95, 31.75), (29.80, 32.45), (29.95, 33.15))):
        pouf(felts[i]).emit(f"Pouf_{i + 1}", lounge, Vector((x - 0.23, y - 0.23, 0)))
    tv_stand().emit("TV_OnWheels", lounge, *lib["placement"](28.55, 32.45, 1.10, 0.62, "+x"))
    return hidden


hidden = build()
print("bank + lounge built; placeholders hidden:", hidden)
