# Fab Lab SAGA — Blender model (project brief for Claude)

Authoritative project state as of 2026-10-08. Read this first; then `git log --oneline` for history,
`LICENSES.md` for asset rules, `SETUP.md` for machine setup. The previous session's full transcript
may also be available (see SETUP.md) — this file is the summary of record.

## What this is
Photoreal architectural model of **Fab Lab SAGA**, a new university Fab Lab (HÍ + Reykjavík/Mixtúra)
opening on the ground floor of **Bændahöllin / old Hótel Saga, Hagatorg 1, 107 Reykjavík**, west end of
the T-shaped building's top bar. Started from a colleague's SketchUp model (`source/SagaV2.skp`,
converted with openskp → `export/`). The user despises SketchUp; all work continues in Blender.
Purpose: impressive presentation renders (stills now; animated walkthrough later on a strong machine).
A later project: a Blender add-on that generates the user's black-profile shelving
(`scripts/profile_furniture.py` is its seed).

## Working style the user expects
- Collaborate; ask (AskUserQuestion) when a decision is theirs; otherwise act. Short, concrete reports.
- They like to SEE work live: drive the open Blender GUI through the MCP add-on (or `scripts/bmcp.py`,
  which talks to the add-on socket 127.0.0.1:9876 directly). Save the live file after each change —
  saving is Claude's job.
- Everything scripted and re-runnable; commit after each step (attribution lines per system prompt).
- **Licensing:** only CC0 (Poly Haven) or the Fab Lab's own material in renders; record every new asset
  in `LICENSES.md` and `assets/polyhaven/CREDITS.md`. The user asked for this to be triple-checked.
- Laptop (old machine) = fast reference renders only (`scripts/render_review.py`, 960x540, 12 spp).
  Finals belong on the powerful machine (`scripts/render_finals.py`, auto-picks the GPU).

## Files
- `SagaV2_work.blend` — **the working file, source of truth** (contains manual tweaks: HDRI world +
  rotation, per-camera `exposure_offset`/`show_ground`/`shot_order`, floor clip, etc.).
- `SagaV2_import.blend` — raw import (regenerate with `scripts/import_glb.py`); never overwrite the work file.
- `scripts/` — builders. Each rebuilds its own collection when exec'd inside Blender
  (`exec(open(path).read())` via MCP). Order if rebuilding several:
  `build_services` → `build_machines` → `build_bank_lounge` → `build_sofas` (ALWAYS after bank_lounge) →
  `build_craft_spine` → `build_life` → `build_microelectronics` → `build_textile` → `build_bank_walls` →
  `build_cupboard` → `cleanup_leftovers` → `build_signs` → `apply_pbr` → `detail_materials` → `fix_glass` → `add_cameras`.
  Helpers: `profile_furniture.py` (shelf_unit/table_unit, omit= for desk niches), `build_demo.py`,
  `mural.py` (SVG mural generator), `sun.py` (solar position), `fetch_polyhaven.py`,
  `render_review.py` (3x3 review sheet), `render_finals.py` (all cameras with shot_order),
  `bmcp.py` (MCP-socket fallback), `import_glb.py`.
- `assets/` — CC0 textures/models/HDRI (HDRI .exr is git-ignored: re-fetch `buikslotermeerplein` 4k exr
  from Poly Haven into `assets/polyhaven/hdri/` if missing), mural, signs.
- `refs/` — branding (Fab Lab Ísland brand manual 2021, signs, logos, Roboto fonts), equipment list PDF
  (the machinery list given to the architects for electrical load + airflow), user photos.
- `renders/final2/` — 21 stills at 1920x1080 (CPU, 32 spp). `renders/tmp/` — scratch previews.

## Geometry & site facts (verified)
- Model units metres. Frame: **+Y = ESE (bearing 116°), −Y = WNW, +X = SSW (sunny façade, 206°),
  −X = NNE.** Never say north/south for plan up/down. Viewer facing −Y has +X on their LEFT.
- Scale verified: column grid 8.40 m = architects' elevation 8.398 m; width 14.99 m = OSM 15 m.
- Heights from Reykjavík drawing archive (Hagatorg 1, 2024 set by Andrúm): floor K13.00, next floor
  K17.20, concrete soffit ≈ 3.93 m clear, glazing to 3.6 m, transom ~3.30.
- Main entrance = SSW glass door at y 35.11–36.21. Sun: 22 Sep 15:30 UTC (az 215°, el 22°) so light
  reaches under the ~1.9 m upper-floor overhang. HDRI rotation aligned to the sun lamp.

## Zones (current layout, user-approved)
- **Laser room** (glazed room by SSW façade, x 29.67–32.53, y 20.14–26.92): Epilog Fusion Edge 24,
  2× Glowforge Pro HD, Glowforge Aura, xTool F1 Ultra on profile laser tables; exhausts out through the
  façade beam, inline fan on the long Epilog run.
- **Print farm** outside the laser room: profile shelving, 12 Prusa MK3S+ (0.58 m shelf pitch), Bambu P2S.
- **CNC room**: ShopBot PRS Alpha 120 against the INTERIOR wall; ACword FT100 dust collector out by the
  far glass corner; flexible hose overhead. (Clearance ignored per user.) No SRM-20s here.
- **Microelectronics** (ESE side of the tool-wall row): tool walls refitted with drawer cabinets, tool
  rails, wire spools, multimeters; bench with **2× Roland SRM-20 (the only machines here)**, soldering
  stations + fume extractors, scope/PSU. Component storage with DRAWER units on the NNE glass
  (y 30.3–34.1). Electronics commons on the bank wall: pin-up board, whiteboard, cable pegboard, kit
  shelf, 3.2 m teaching table + 6 chairs.
- **Hand-tool wall** on the NNE glass (y 23.25–26.40): pegboard + shelves + counter + tool chest.
  Rule: along glass = varied tool wall + storage WITH A TABLE BELOW, not plain shelving.
- **Felt wall**: Flöff-style recycled-textile felt panels (manual orange/green/blue) on the WNW (bench)
  side of the tool walls; arched tops on the manual's 6x6 grid. NEVER a single raised rounded peak
  between lower shoulders.
- **Work tables** (colleague's benches) with stools, cutting mats, laptops etc.; vinyl cutters on rolling
  stands by the NNE glass.
- **Textile area** (WNW side of the felt, x 26.1–28.9, y 26.6–29.6): sewing table with sewing /
  embroidery / overlock + 4 profile chairs; cutter counter (Cricut, Mayku) against the felt.
- **Lounge / entryway** (SSW glass by the entrance): Cleveland-style sofas, profile coffee tables, felt
  poufs, TV on wheels, bookcase spine. No machines here.
- **Demo display** (back-wall bays visible from the entrance, x ~27.4–32.4): imaginary Fab Lab projects,
  pink neon "make anything". Spine's workshop side also shows projects.
- **Búnaðarbankinn** (equipment bank): STAFF ONLY, boxes only (SAMLA-style), enclosed by walls 2.80 m
  high (NOT to the slab); south wall moved to y 34.32–34.40; only entry = SECRET DOOR hidden in the
  birch-fin relief sculpture facing the entrance (y 36.62–37.58). Standing desk = a niche/gap in the
  back-wall shelving (no chairs). Nothing from the bank accessible outside it.
- **Mural-wall cupboard** (`build_cupboard.py`, x 24.32–25.70 against the mural wall): replaced the
  colleague's sink (hidden). Low 40x40 profile cupboard, birch top 0.905 m, door bay + 3 drawers.
- Accent wall: generated brand mural (`scripts/mural.py`) on the partition by the small rooms; red arch
  portal around its door; logo "FAB LAB SAGA". Signs from the manual placed per zone (`build_signs.py`).

## Look rules
- Photorealism (user's choice). It's a LAB, not a house: no rugs, no indoor plants, no homey décor.
- Brand colours = manual hex exactly (red #E03A3F, green #009967, blue #1245DE, orange #FFA13D,
  yellow #F2C200, pink #E099AB); fix appearance via view transform (AgX Punchy), not material colours.
- Black anodised 20x20 / 40x40 T-slot profile + birch ply = the furniture language. Tables prefer to be
  integrated as gaps in shelving.
- Glass panes are zero-thickness planes: `Glass_Clear` must stay THIN glass (`fix_glass.py`: transparent +
  back-face-corrected Fresnel gloss). Never a refractive/IOR>1 transmission shader on them (warps the view).
- Raw concrete ceiling (`Concrete_Exposed` = Poly Haven concrete_floor_worn_001 + formwork joints; NOT
  concrete_slab_wall, whose bands read as timber), birch ply = Poly Haven plywood colour-corrected pale (hsv in apply_pbr),
  galvanised services, round black enamel pendants, worn oak parquet.

## Open items
- On-site 360° photo for the window view → `refs/skybox/` (current HDRI is a CC0 stand-in).
- Colleague to confirm CNC model (list: PRS Alpha 120; his model had 96x60).
- Brand sign typos in the source files: "VERKÆRI" (missing F), "ELECTRONCS".
- Spine project shelves past the moved bank wall face the wall (offer: shorten the spine).
- Upper hotel floors not modelled → keep exterior shots tight.
- Finals + animated walkthrough on the powerful machine.
