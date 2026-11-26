# Machines from the lab's teaching wikis

The lab's machine wikis (Magnús's own repos, written by his agents) describe each machine as a list of 3D primitives
for their WebGL figures. These JSON files are that list, exported by the wiki's own generator, and
`scripts/wiki_machine.py` rebuilds it as script-built Blender geometry. No external meshes.

| File | Source | Export |
|---|---|---|
| `shopbot_prsalpha_144_60.json` | github.com/MagnusPetursson/shopbot-prsalpha-wiki, `generator/figures/shopbot/build.mjs` (commit in the file's `commit` field) | `build.mjs` with the `MESH` list written out at the end, plus the live cable/hose routes at the rest pose (routes.mjs + the kit's fillet) and the static extras gl-live.js adds (control-box LEDs, LED strip, VFD screen); materials resolved per part with gl-live.js's `MATS`/`MAT_RULES` |

Re-export (Talos, MPDESKTOP): `~/Documents/AgentWork/wiki-models/` holds the clone, `build_export.mjs` (a copy of
build.mjs with the export appended) and `export_mats.mjs`:

    EXPORT_PATH=$PWD/shopbot_mesh.json node shopbot-prsalpha-wiki/generator/figures/shopbot/build_export.mjs
    node export_mats.mjs shopbot_mesh.json shopbot-prsalpha-wiki/generator/figures/shopbot/gl-live.js \
        <SagaModel>/assets/wiki/shopbot_prsalpha_144_60.json $(git -C shopbot-prsalpha-wiki rev-parse --short HEAD)

Units cm, z up; wiki frame: machine X along -x, Y along -y. build_machines.py rotates it +90 deg into the room.
