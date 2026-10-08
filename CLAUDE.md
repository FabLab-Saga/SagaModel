# Fab Lab SAGA — Blender model (project brief for Claude)

Authoritative project state as of 2026-10-08 (MPDESKTOP; PLAN.md G1–G11 done). Read this first; then `git log --oneline` for history,
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
  `build_services` → `build_lighting` → `build_machines` → `build_laser_room` → `build_bank_lounge` → `build_sofas` (ALWAYS after bank_lounge) →
  `build_craft_spine` → `build_life` → `build_microelectronics` → `build_textile` → `build_bank_walls` →
  `build_cupboard` → `cleanup_leftovers` → `build_material_storage` → `build_hall_entrance` → `build_signs` → `apply_pbr` → `detail_materials` → `fix_glass` → `add_cameras`.
  Helpers: `profile_furniture.py` (shelf_unit/table_unit, omit= for desk niches), `build_demo.py`,
  `mural.py` (SVG mural generator), `sun.py` (solar position), `fetch_polyhaven.py`,
  `render_review.py` (3x3 review sheet), `render_finals.py` (all cameras with shot_order),
  `bmcp.py` (MCP-socket fallback), `import_glb.py`.
- `assets/` — CC0 textures/models/HDRI (HDRI .exr is git-ignored: re-fetch `buikslotermeerplein` 4k exr
  from Poly Haven into `assets/polyhaven/hdri/` if missing), mural, signs.
- `refs/` — branding (Fab Lab Ísland brand manual 2021, signs, logos, Roboto fonts), equipment list PDF
  (the machinery list given to the architects for electrical load + airflow), user photos.
- `renders/final3/` — 29 stills at 1920x1080 (GPU OptiX, 128 spp) after the PLAN.md goals G1–G11 (2026-10-08).
  `renders/final2/` — older set (pre-G1, CPU 32 spp). `renders/tmp/` — scratch previews.

## Geometry & site facts (verified)
- Model units metres. Frame: **+Y = ESE (bearing 116°), −Y = WNW, +X = SSW (sunny façade, 206°),
  −X = NNE.** Never say north/south for plan up/down. Viewer facing −Y has +X on their LEFT.
- Scale verified: column grid 8.40 m = architects' elevation 8.398 m; width 14.99 m = OSM 15 m.
- Heights from Reykjavík drawing archive (Hagatorg 1, 2024 set by Andrúm): floor K13.00, next floor
  K17.20, concrete soffit ≈ 3.93 m clear, glazing to 3.6 m, transom ~3.30.
- Main entrance = door at y 35.11–36.21 on the SSW line. It opens onto the HOTEL'S MAIN HALL (inside Bændahöllin),
  not the street: `Cam_HallEntrance` (was Cam_ExteriorEntrance) is an interior hall view; hall-side signage in
  `build_hall_entrance.py` (fascia sign with the Fab Lab icon SVG, plaque, door vinyl). Sun: 22 Sep 15:30 UTC (az 215°, el 22°) so light
  reaches under the ~1.9 m upper-floor overhang. HDRI rotation aligned to the sun lamp.

## Zones (current layout, user-approved)
- **Laser room** (glazed room by SSW façade, x 29.67–32.53, y 20.14–26.92; `build_laser_room.py`, collection
  LaserRoom; machine MODELS in build_machines.py, checked against the equipment list): 4.86 m profile laser bench on the
  SSW glass (flat-file sheet drawers under) with 2× Glowforge Pro HD, Glowforge Aura (orange lid), xTool F1 Ultra (UPRIGHT
  green-shield galvo tower 273x373x492 + separate touchscreen controller; checked against xTool photos) +
  1.3 m staging; Epilog Fusion Edge 24 floor unit at the NNE/WNW corner (0.20 m off the partition, riser behind);
  laser stock rack (upright sheet slots, 0.98 m worktop, bins/rolls) on the NNE partition; 2 m standing prep counter
  under the interior window; safety station + 3 offcut bins on the WNW wall. ONE central exhaust (`Exhaust_Central`):
  rear ports → manifold behind the bench → riser (y 25.17) → ceiling collector (Epilog branch joins) → inline fan →
  up through the slab to the building's vent. Keep both doors and a ≥1.0 m aisle clear.
- **Print farm** outside the laser room: profile shelving, 12 Prusa MK3S+ (0.58 m shelf pitch), Bambu P2S.
- **CNC room**: ShopBot PRS Alpha 120 against the INTERIOR wall; ACword FT100 dust collector out by the
  far glass corner; ribbed hose on a ceiling-hung swing boom (`ShopBot_DustBoom`), brush skirt on the spindle.
  (Clearance ignored per user.) No SRM-20s here.
  **Material storage** (`build_material_storage.py`): rolling sheet cart (ply/MDF/acrylic) at the ShopBot's
  loading end (x 22.35–24.90, y 16.95–18.25), offcut slot rack + cantilever rod rack on the side wall x 25.74.
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
- **Lounge** (by the SSW glass): ONE small circular conversation nook (`nook()` in build_bank_lounge.py, centre
  30.95/31.60, 2.85 m): 240° curved charcoal sofa (back to the glass, open towards the spine path), felt cushions,
  round birch table, 2 felt poufs. No TV, no machines. Keep walkways clear (spine path ≥1.2 m, entrance zone,
  strip along the glass). `build_sofas.py` is now a no-op (no Cleveland sofas left).
- **Demo display** (back-wall bays visible from the entrance, x ~27.4–32.4): imaginary Fab Lab projects,
  hex-tile art relief above. Spine's workshop side also shows projects.
- **Búnaðarbankinn** (equipment bank): STAFF ONLY, boxes only (SAMLA-style), enclosed by walls 2.80 m
  high (NOT to the slab); south wall moved to y 34.32–34.40; only entry = SECRET DOOR hidden in the
  birch-fin relief sculpture facing the entrance (y 36.62–37.58). Standing desk = a niche/gap in the
  back-wall shelving (no chairs). Nothing from the bank accessible outside it. Shelf-high (2.42 m) birch privacy
  backs behind the shelving along the NNE glass and the ESE back wall (`Bank_PrivacyBacks`): no looking in.
  Packing table (`Bank_PackingTable`, 3.0x0.70 m, 0.92 m standing, no stools) centred at (24.50, 36.275). RULE: keep
  >=1.1 m free in front of every shelf run (lifting a huge box off a bottom shelf) and >=1.2 m by the secret door.
- **Mural-wall cupboard** (`build_cupboard.py`, x 24.32–25.70 against the mural wall): replaced the
  colleague's sink (hidden). Low 40x40 profile cupboard, birch top 0.905 m, door bay + 3 drawers.
- Accent wall: generated brand mural (`scripts/mural.py`) on the partition by the small rooms; red arch
  portal around its door; logo "FAB LAB SAGA".
- **Art piece** above the demo bays (`hex_relief` in build_demo.py): ~700 3D-printed hex tiles, brand gradient,
  wave depths, lit by `Art_Spot`. Replaced the "make anything" neon (user: ugly, cliché - no neon signs). Signs from the manual placed per zone (`build_signs.py`).

## Look rules
- Photorealism (user's choice). It's a LAB, not a house: no rugs, no indoor plants, no homey décor.
- Brand colours = manual hex exactly (red #E03A3F, green #009967, blue #1245DE, orange #FFA13D,
  yellow #F2C200, pink #E099AB); fix appearance via view transform (AgX Punchy), not material colours.
- Shading: builder emits use auto-smooth (smooth + sharp edges > 30°). Blender 5.2 bmesh output is smooth-shaded by
  default, which made flat boxes shade like blobs. Model real products from PHOTOS, not memory.
- Black anodised 20x20 / 40x40 T-slot profile + birch ply = the furniture language. Tables prefer to be
  integrated as gaps in shelving.
- Glass panes are zero-thickness planes: `Glass_Clear` must stay THIN glass (`fix_glass.py`: transparent +
  back-face-corrected Fresnel gloss). Never a refractive/IOR>1 transmission shader on them (warps the view).
- Raw concrete ceiling (`Concrete_Exposed` = Poly Haven concrete_floor_worn_001 + formwork joints; NOT
  concrete_slab_wall, whose bands read as timber), birch ply = Poly Haven plywood colour-corrected pale (hsv in apply_pbr),
  galvanised services, worn oak parquet. LIGHTING (`build_lighting.py`): suspended black linear LED arrays
  (bottom 2.95 m, rows dodge services/felt/boom) + angled track spots on mural, felt, nook, demo. NO pendants.
  Scene exposure +0.8 EV (was +1.4 with the old pendants).

## Open items
- On-site 360° photo for the window view → `refs/skybox/` (current HDRI is a CC0 stand-in).
- Colleague to confirm CNC model (list: PRS Alpha 120; his model had 96x60).
- Brand sign typos in the source files: "VERKÆRI" (missing F), "ELECTRONCS".
- Spine project shelves past the moved bank wall face the wall (offer: shorten the spine).
- Upper hotel floors not modelled → keep exterior shots tight.
- CNC room's WNW end (y ≈15.08) has a 2.3 m unglazed opening (x 22.4–24.7) to outdoors in the colleague's
  model — ask the user: loading door, glazing, or wall?
- Animated walkthrough (stills done on MPDESKTOP: RTX 4070 Ti SUPER, OptiX; ~10-25 s per 1080p still).
- Spine has no camera on its workshop face; the demo pieces there are only seen in passing.
