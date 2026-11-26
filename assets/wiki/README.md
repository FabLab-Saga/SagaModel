# Machines from the lab's teaching wikis

The lab's machine wikis (Magnús's own repos, written by his agents) describe each machine as a list of 3D primitives
for their WebGL figures. These JSON files are that list, exported by the wiki's own generator, and
`scripts/wiki_machine.py` rebuilds it as script-built Blender geometry. No external meshes.

| File | Source | Export |
|---|---|---|
| `epilog_fusion_edge_24.json` | github.com/MagnusPetursson/epilog-fusion-edge-24-wiki, `generator/gl/model.mjs` `build()` | the generator's own triangle arrays per moving group (static, lid, bridge, head, table, stock; mm, X right, Y rear, Z up) + part list + material table: `node export_epilog.mjs <dest> <commit>`; placed by `scripts/wiki_machine.py` `wiki_tri_part()` with the viewer's group offsets |
| `xtool.json`, `srm20.json` | the coordinator host's `~/Documents/AgentWork/saga-wiki-xtool/wiki` and `saga-wiki-srm20/site` (no git; snapshot 2026-11-26), `generator/gl/machine.gl.mjs` via `geom.mjs` `tessellate()` | `node export_glwiki.mjs <wiki dir> <dest> <stamp>`: triangles per group + each group's HOME translation from `GROUPS`/`CHANNELS` (used by default) |
| `shopbot_prsalpha_120_60.json` | github.com/MagnusPetursson/shopbot-prsalpha-wiki, `generator/figures/shopbot/build.mjs` at 0b68547 (the wiki's 144-60), re-run as HÍ's actual PRSalpha 120-60 with `shopbot_120_60.patch` (table 358.1 cm, travel 327.7 cm, legs/bearers/control box/x-chain respaced; parts keep their size) | `build.mjs` with the `MESH` list written out at the end, plus the live cable/hose routes at the rest pose (routes.mjs + the kit's fillet) and the static extras gl-live.js adds (control-box LEDs, LED strip, VFD screen); materials resolved per part with gl-live.js's `MATS`/`MAT_RULES` |

Re-export (Talos, MPDESKTOP): `~/Documents/AgentWork/wiki-models/` holds the clone, `build_export.mjs` (a copy of
build.mjs with the export appended) and `export_mats.mjs`:

    # sb120/ = a copy of the clone's generator/ with shopbot_120_60.patch applied
    EXPORT_PATH=$PWD/sb120/shopbot_mesh.json node sb120/generator/figures/shopbot/build_export.mjs
    node export_mats.mjs sb120/shopbot_mesh.json sb120/generator/figures/shopbot/gl-live.js \
        <SagaModel>/assets/wiki/shopbot_prsalpha_120_60.json 0b68547+local-120-60

Once MPTVPC's 120-60 correction of the wiki is pushed (asked 2026-11-26), re-export from that commit and drop the patch.

Units cm, z up; wiki frame: machine X along -x, Y along -y. build_machines.py rotates it +90 deg into the room.
