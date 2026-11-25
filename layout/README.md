# Layout files (contract v1)

Owner of the format: Talos (MPDESKTOP). v1 is contract v0 plus a few additive fields; nothing in v0 was renamed or
removed. Changes to field names are posted to Hermes on MPTVPC (the 2D planner follows this file).

| File | Who writes it | What it is |
|---|---|---|
| `layout.yaml` | Magnús, the planner (branch `layout/drafts`), Talos | Item placements. The ONLY source of positions. |
| `room.json` | `scripts/layout_export.py` (Blender) | Fixed architecture + constraints. Read-only for everyone else. |
| `TRUTH.md` | Talos with Magnús | What the real lab is, item by item, with dates; open questions. |

## Frame

Blender model coordinates, metres. +Y = ESE (bearing 116°), −Y = WNW, +X = SSW (sunny façade), −X = NNE. Never call
plan directions north/south. Rotation in degrees about +Z, counter-clockwise seen from above. A top-down plan with
+Y to the right has +X pointing DOWN (the SSW façade at the bottom); `scripts/layout_plan_png.py` draws it that way.

## layout.yaml

A YAML file restricted to: a top-level map with `version` and one `items` list of flat maps; values are numbers,
true/false, null, plain or double-quoted strings, and inline lists (`[x, y]`). Comments are fine. Any YAML parser reads
it; `scripts/layout_io.py` reads and writes it without PyYAML and keeps the field order.

```yaml
version: 1
items:
  - id: laser.glowforge-prohd-1   # stable, unique, lowercase, zone prefix; never reused or renamed
    label: Glowforge ProHD 1      # shown in the planner; free to edit
    kind: machine                 # machine | furniture | storage | fixture
    zone: laser-room              # zone id from room.json
    pos: [32.143, 20.792]         # footprint centre [x, y] (m)
    z: 0.78                       # base height (m); items on a bench carry the bench top height
    rot: -90                      # degrees CCW about +Z
    size: [0.957, 0.57, 0.215]    # w (item's own x), d (own y), h (m); measured, refreshed by the exporter
    "on": laser.laserbench        # optional parent item (key quoted: YAML 1.1 reads bare on as true); pos still absolute
    locked: false                 # true = fixed by architecture/services; planner shows it, refuses drag
    machine: glowforge            # optional website slug (fablab-saga-website)
    count: 1                      # optional
    note: ""                      # optional free text (Magnús or Talos)
    objects: [Glowforge_ProHD_1]  # v1 addition: Blender root objects moved as one; first = primary
```

Rules:

- **Edit `pos`, `rot`, `z` (and `label`/`note`) only.** `size` is measured from the model and overwritten by the
  exporter; `objects` belongs to Talos. Moving a parent does not move its `on:` children in the file. The planner
  should move them along (same delta) and Blender users should select both, otherwise the snapshot reports the child as left behind.
- **`pos` is the footprint centre, not the Blender origin.** It is measured from the geometry: the bounding box of all
  `objects` (and children) in the primary object's rotation frame. That makes it independent of how a builder placed
  its origin (several objects are built in world coordinates with the origin at 0,0).
- New item: add an entry without `objects`. The snapshot reports it as `added`; Talos builds or links the object.
- Removing an item: delete the entry; the snapshot reports `removed`. Talos removes or hides it in the model.
- Precision: pos is written to the millimetre. Blender applies an item only if it differs by more than 0.8 mm / 0.06°,
  so an unchanged file leaves the scene bit-identical.

## room.json

Generated; regenerate with `blender -b SagaV2_work.blend --python scripts/layout_export.py`. v0 fields, plus:

- `frame`, `section_height` (walls are a plan section at 1.1 m through the evaluated model, booleans applied).
- `walls[]`: `{id, kind: wall|glazing|glass-partition, a, b, t}` centrelines with thickness `t`. Wall ids are
  regenerated each export: don't store them.
- `doors[]`: v0 fields plus `source: drawing|model|assumed` (assumed = hinge/swing not checked) and `note`.
  `side` is a point on the room side of the door; `swing: in` opens towards `side`.
- `columns[]`: `{id, pos, size, shape, source: section|grid}` (grid = completed from the 8.40 m column grid where a
  column is buried in a wall).
- `zones[]`: plus `source` (where the boundary comes from; "approx" = drawn by Talos from walls/furniture).
- `keepout[]`: door swing quarter-discs for every door; `escape route` strips (`door_clear` deep, both sides) at the
  entrance and the escape doors. Plus `door`: the door id. The full escape route is not drawn yet (see TRUTH.md).
- `services[]`: only what the model knows (laser exhaust riser, water at the staff kitchen and WC). Power and data
  outlets are not modelled.
- `rules`: `walkway_min` 1.2, `aisle_laser_min` 1.0, `door_clear` 0.9 (m).

## Snapshot (`scripts/layout_snapshot.py`)

Compares a TARGET against the BASE layout (default base = `layout.yaml` at git HEAD):

```bash
python3 scripts/layout_snapshot.py                  # target = live Blender (MCP socket 9876) if open, else working-tree yaml
python3 scripts/layout_snapshot.py --blend FILE     # target = a saved .blend, measured headless
python3 scripts/layout_snapshot.py --yaml FILE      # target = another layout.yaml (e.g. the planner's)
python3 scripts/layout_snapshot.py --ref layout/drafts --base main   # git refs
python3 scripts/layout_snapshot.py --json           # machine-readable (contract format)
python3 scripts/layout_snapshot.py --write          # also write the target poses into layout.yaml (accept the moves)
```

JSON: `{"base", "target", "moves": [{id, from: {pos, rot, z}, to: {...}, dist, drot}], "added": [...],
"removed": [...], "violations": [{rule, items, value, where}]}`. Text: one line per move, e.g.
`lab.worktable-1 moved 1.12 m towards +X (SSW) / -Y (WNW), rotated +90°`.

Violations are checked for moved and added items only: overlap with another floor item, keepout intrusion
(door swing / escape route), clearance under `walkway_min` (`aisle_laser_min` in the laser room) to a neighbour or wall, item outside its zone,
`on:` child not moved with its parent, moving a `locked` item.

## Blender side

- `scripts/layout_blender.py`: `apply([collection])`, `poses()`, `measure()`, `parent_items()`. Every item builder
  ends with `apply()`. `apply()` first parents companions to their primary (same collection only) and `on:` children
  to their host (also across builders), keeping world transforms, so dragging a bench in the GUI carries what stands
  on it; the snapshot then reports the children as "moved with <host>".
- Checks: `layout_check_identity.py` (apply an unchanged yaml: 0 objects change), `layout_check_rebuild.py` (re-run all
  16 item builders, compare all 2,506 objects; 2026-11-25: 0.0 mm / 0.0 deg, every item within 0.71 mm of the yaml,
  i.e. its mm rounding). A builder may lay out its own contents differently after its host moved (build_life
  re-lays bench props on a rotated table); the item still lands on its yaml pose.
- `layout_export.py` refreshes room.json and adds new builder objects to the yaml without touching existing
  placements (`--fresh` regenerates everything; don't use it once people edit the file).

## Flow

1. Magnús moves things in Blender (or the planner). Blender: save, then `layout_snapshot.py --write` on a
   `layout/drafts` checkout, commit `layout: <summary>`. Planner: commits to `layout/drafts` itself.
2. Talos reads `main..layout/drafts`, posts the intent read-back, polishes, merges to `main`.
3. Builders (`scripts/build_*.py`) build at their own coordinates and finish with `apply(<collection>)`, so a rebuild
   always lands on the positions in `layout.yaml`. `scripts/layout_check_identity.py` proves an unchanged file is a no-op.
4. Publishing the public web preview is separate and release-only (tag `web-vN`, Magnús's yes per release).
