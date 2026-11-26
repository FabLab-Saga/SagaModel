"""Lock-down kit: the one acrylic-door + electronic-cabinet-lock detail every enclosure uses (Talos's design,
2026-11-25; Magnús: acrylic doors, electronic locks where reasonable). Self-contained (own materials); exec it into any builder namespace:

    exec(open(HERE + "lockdown.py").read(), globals())

World-space helpers on a Part (axis-aligned, `face` = the direction the door's outside faces: "+x", "-x", "+y", "-y"):
    acrylic_door(p, face, plane, a0, a1, z0, z1, hinge="a"|"b", lock=True)   one leaf in the plane `plane`
    door_run(p, face, plane, a0, a1, z0, z1, leaves)                          n leaves, paired, one lock per pair
    elock(p, face, plane, a, z)                                               RFID reader pad on the outside, lock
                                                                              body behind (powered, 12 V)
The lock is a surface RFID cabinet lock: slim black reader pad (45 x 85 mm) with a status LED, the bolt body on the
inside; the same position takes a mechanical cam lock if the lab prefers keys for a door.
"""
import bpy


def _ld_mat(name, hexcol, rough=0.4, emit=0.0, alpha=1.0, coat=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)        # values re-applied on every rebuild
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    h = hexcol.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]      # sRGB -> linear
    b.inputs["Base Color"].default_value = (*c, 1)
    b.inputs["Roughness"].default_value = rough
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emit:
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "BLENDED"
    m.diffuse_color = (*c, alpha)
    return m


def _ld_mats():
    acr = bpy.data.materials.get("Acrylic_Door") or _ld_mat("Acrylic_Door", "#C9D6DC", 0.03, alpha=0.07, coat=0.8)
    pad = _ld_mat("ELock_Pad", "#141517", 0.35)
    led = _ld_mat("ELock_LED", "#2BD46A", 0.3, emit=4.0)
    body = _ld_mat("ELock_Body", "#2A2C2F", 0.45)
    edge = _ld_mat("Acrylic_Edge", "#B4CDD2", 0.08, coat=0.6)                    # polished edge: the glint that reads
    return acr, pad, led, body, edge


def _box(p, m, face, plane, a0, a1, z0, z1, n0, n1):
    """Box spanning a0..a1 along the door plane, z0..z1, and n0..n1 outward from `plane` (outside = +n)."""
    s = 1 if face[0] == "+" else -1
    t0, t1 = sorted((plane + s * n0, plane + s * n1))
    if face[1] == "x":
        p.box(m, t0, t1, a0, a1, z0, z1)
    else:
        p.box(m, a0, a1, t0, t1, z0, z1)


def elock(p, face, plane, a, z, t=0.005):
    """Electronic cabinet lock at (a along the door, height z) on a door of thickness t lying at `plane`."""
    _, pad, led, body, _ = _ld_mats()
    _box(p, pad, face, plane, a - 0.0225, a + 0.0225, z - 0.0425, z + 0.0425, t, t + 0.011)       # reader pad
    _box(p, led, face, plane, a - 0.004, a + 0.004, z + 0.028, z + 0.033, t + 0.011, t + 0.0118)  # status LED
    _box(p, body, face, plane, a - 0.030, a + 0.030, z - 0.050, z + 0.050, -0.032, 0.0)            # bolt body


def acrylic_door(p, face, plane, a0, a1, z0, z1, hinge="a", lock=True, lock_z=None, handle=True, t=0.005):
    """One clear acrylic leaf (5 mm, polished edges) between a0..a1 and z0..z1, hinge edge at a0 ("a") or a1 ("b");
    two black hinges on the hinge edge, a black edge pull on the free edge and the electronic lock beside it."""
    acr, pad, _, body, edge = _ld_mats()
    blk = bpy.data.materials.get("Alu_Black_Anodized") or pad
    _box(p, acr, face, plane, a0 + 0.002, a1 - 0.002, z0, z1, 0.0, t)
    for zz in (z0, z1 - 0.004):                                                       # polished edges all round,
        _box(p, edge, face, plane, a0 + 0.002, a1 - 0.002, zz, zz + 0.004, 0.0, t)    # so the leaf reads as a door
    for aa in (a0 + 0.002, a1 - 0.006):                                               # (not a pull on what is behind)
        _box(p, edge, face, plane, aa, aa + 0.004, z0, z1, 0.0, t)
    ha = a0 + 0.012 if hinge == "a" else a1 - 0.012
    fa = a1 - 0.045 if hinge == "a" else a0 + 0.045
    for zz in (z0 + 0.06, z1 - 0.10):
        _box(p, blk, face, plane, ha - 0.012, ha + 0.012, zz, zz + 0.045, -0.004, t + 0.006)
    zm = lock_z if lock_z is not None else (z0 + z1) / 2
    if handle:                       # edge pull: black alu profile clamped on the free edge (140 mm), level with the
        ea = a1 - 0.002 if hinge == "a" else a0 + 0.002      # lock. A bar pull on the face sat on the centre line of
        e0, e1 = (ea - 0.012, ea) if hinge == "a" else (ea, ea + 0.012)   # a drawer behind and read as its handle.
        _box(p, blk, face, plane, e0, e1, zm - 0.07, zm + 0.07, -0.002, t + 0.016)
        lip = (e0 - 0.010, e0) if hinge == "a" else (e1, e1 + 0.010)
        _box(p, blk, face, plane, lip[0], lip[1], zm - 0.07, zm + 0.07, t + 0.012, t + 0.016)   # finger lip
    if lock:
        la = fa - 0.045 if hinge == "a" else fa + 0.045
        elock(p, face, plane, la, lock_z if lock_z is not None else (z0 + z1) / 2, t)


def door_run(p, face, plane, a0, a1, z0, z1, leaves=2, lock_z=None):
    """`leaves` equal leaves across a0..a1, hung in pairs that meet in the middle (left leaf hinged left, right leaf
    hinged right); each pair shares one lock on its right leaf; an odd last leaf gets its own."""
    w = (a1 - a0) / leaves
    for i in range(leaves):
        b0, b1 = a0 + i * w, a0 + (i + 1) * w
        left = (i % 2 == 0)
        last_single = left and i == leaves - 1
        acrylic_door(p, face, plane, b0, b1, z0, z1, hinge="a" if left else "b",
                     lock=(not left) or last_single, lock_z=lock_z)
