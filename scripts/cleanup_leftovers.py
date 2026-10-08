"""Hide leftover pieces of the colleague's SketchUp model that clash with the current layout. Re-runnable.

- Component_1346962.003: a 4th OSB tool wall (hammers + saws) standing by the CNC dust collector, y 15.3-15.8.
- aluminum_extrusion.034-.041 + the root Plywood_4x8_Sheet_3_4_tex: a small profile table buried in the
  electronics component storage on the NNE glass (x 21.0-21.5, y 31.1-33.4); its board stuck out of the drawers.
- aluminum_extrusion.012-.031: a bare 3 m profile frame at x 27.2-28.0, y 29.8-30.6 (nothing rests on it).
- Component_289785, .001, .002: the colleague's shelf units on the bank back wall (y 37.8-38.3), boards and all;
  the bank's own shelving stands there (their boards poked out above it up to 3.05 m).
Hidden, never deleted (same pattern as the other builders).
"""
import bpy

NAMES = ["Component_1346962.003", "Plywood_4x8_Sheet_3_4_tex", "Component_289785", "Component_289785.001",
         "Component_289785.002"]
NAMES += [f"aluminum_extrusion.{i:03d}" for i in list(range(12, 32)) + list(range(34, 42))]


def build():
    n = 0
    for name in NAMES:
        o = bpy.data.objects.get(name)
        if o is None:
            print("missing", name)
            continue
        for k in (o, *o.children_recursive):
            k.hide_render = k.hide_viewport = True
            n += 1
    print("cleanup_leftovers: hid %d objects" % n)


build()
