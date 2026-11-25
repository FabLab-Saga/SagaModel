# Fab Lab SAGA — Blender model (project brief for Claude)

Authoritative project state as of 2026-10-08 late evening (MPDESKTOP; PLAN.md G1–G11 done; since then: hidden
leftovers deleted, work tables, print-farm cabins, every listed machine modelled (MACHINES.md), on-call desk + Fab Lab
TV, GULLVALLA lounge, back staff area (WC, Kaffistofa, store-room door, hallway glass door), CNC room rebuilt (glass
front with dot manifestation, real-size ShopBot, upright board rack, loading door + windows); entrance moved to the
corner bay per the city drawings + hall set; signs re-lettered; walkthrough v1 animatic). Now: the presentation video
(see RENDER.md). This file is Claude's own file (Magnús): keep it current in every commit, no permission needed. `AGENTS.md` is a symlink to this file (Hermes/Codex/Claude Code all read it). Read this first; then
`git log --oneline` for history, `LICENSES.md` for asset rules, `SETUP.md` for machine setup (partly written for the
old laptop). Hermes session "Fab lab Blender" (`hermes --continue "Fab lab Blender"`) holds the 2026-10-08 work —
this file is the summary of record.

## What this is
Photoreal architectural model of **Fab Lab SAGA**, a new university Fab Lab (HÍ + Reykjavík/Mixtúra)
opening on the ground floor of **HÍ - Saga (the University of Iceland's Saga building, old Hótel Saga; "Bændahöllin" is
an antiquated name - never use it in visible text), Hagatorg 1, 107 Reykjavík**, west end of
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
- **Move the user's visible viewport to whatever you are working on** (set region_3d view_location /
  view_rotation / view_distance, perspective, Rendered shading) at the start of a step and after rebuilds —
  they like seeing results instantly. Headless review renders for verification on top of that.
  Use `scripts/viewport.py` (EYE/TARGET -> all 3D views, Rendered): view_rotation = (target-eye).to_track_quat('-Z','Y').
  With 'Z' instead of '-Z' the view points backwards and the user sees the underside of the floor. Verify with
  `bpy.ops.screen.screenshot_area` (temp_override window/area/region) and look at the PNG.
- Verify visually: `scripts/render_cams.py -- <CamNames>` (review renders, ~5 s each on the GPU) and
  `scripts/peek.py -- eye target out.png lens` (ad-hoc viewpoint); read the PNGs before reporting.
- Real products (machines, furniture) are modelled from PHOTOS (manufacturer pages), never from memory.
  `MACHINES.md` is the machine register: equipment list (PDF) vs model, exact model, image + product links, dims.
  Keep it in sync whenever a machine is added, moved or removed (one Blender object per listed unit).
- Colleague SketchUp objects: builders hide what they replace; `purge_hidden.py` then DELETES every render-hidden
  object (keeps the façade boolean cutters + per-camera ground, and any datablock a builder looks up by name, e.g.
  the `Profile_2020/4040` template meshes). Never delete a template mesh profile_furniture needs.
- Push after each commit (remote: github.com/MagnusPetursson/SagaModel, private).
- Everything scripted and re-runnable; commit after each step (attribution lines per system prompt).
- **Licensing:** only CC0 (Poly Haven) or the Fab Lab's own material in renders; record every new asset
  in `LICENSES.md` and `assets/polyhaven/CREDITS.md`. The user asked for this to be triple-checked.
- MPDESKTOP (RTX 4070 Ti SUPER, OptiX) is the render machine: finals via `scripts/render_finals.py`
  (`SAGA_OUT=final3 SAGA_SPP=128`, ~15 s per 1080p still). The old laptop only did quick references.

## Files
- `SagaV2_work.blend` — **the working file, source of truth** (contains manual tweaks: HDRI world +
  rotation, per-camera `exposure_offset`/`show_ground`/`shot_order`, floor clip, etc.).
- `SagaV2_import.blend` — raw import (regenerate with `scripts/import_glb.py`); never overwrite the work file.
- `scripts/` — builders. Each rebuilds its own collection when exec'd inside Blender
  (`exec(open(path).read())` via MCP). Order if rebuilding several:
  `build_services` → `build_lighting` → `build_machines` → `build_print_farm` → `build_laser_room` → `build_bank_lounge` →
  `build_sofas` (ALWAYS after bank_lounge) → `build_craft_spine` → `build_worktables` → `build_life` (needs WorkTables) →
  `build_microelectronics` → `build_textile` → `build_bank_walls` → `build_cupboard` → `cleanup_leftovers` →
  `build_material_storage` → `build_entrance_bay` → `build_hall_entrance` → `build_welcome` → `build_staff_area` → `build_cnc_room` → `build_signs` → `apply_pbr` → `detail_materials` → `fix_glass` →
  `add_cameras` → `purge_hidden`.
  Builders added 2026-10-08: `build_lighting` (LED arrays + spots), `build_laser_room` (laser room incl. central
  exhaust; machine models live in build_machines), `build_cupboard` (mural-wall cupboard), `cleanup_leftovers`
  (hides colleague leftovers), `build_material_storage` (CNC room stock), `build_hall_entrance` (hall signage),
  `fix_glass` (thin-glass shader), `build_worktables` (2x2 work tables + chairs), `build_print_farm` (printer wall with
  cabins), `build_welcome` (on-call desk + Fab Lab TV), `build_staff_area` (back WC, staff room, store-room door,
  `Cut_WC2` boolean = the demolished second WC; its `door_in_wall()` sets a normal framed door into any colleague
  opening and closes the wall above), `build_cnc_room` (CNC glass front + manifestation, hallway/loading doors, end
  windows, hallway glass end door, outdoor paving, operator corner; `Cut_CNC_*` booleans), `purge_hidden` (deletes
  hidden leftovers). Boolean cutters live in Facade_Cutters, render-hidden AND viewport-hidden (`hide_set(True)`),
  else the Rendered viewport draws them as solid blocks. ALL machine models (incl. CR-200B, AD5M Pro, CR-10 Max, Eazao,
  handheld scanner, red clam press, LOKLiK, EasyPress, Mug Press, BEKANT cart) are functions in build_machines.py; zone builders place them.
  Helpers: `profile_furniture.py` (shelf_unit/table_unit, omit= for desk niches), `build_demo.py`,
  `mural.py` (SVG mural generator), `sun.py` (solar position), `fetch_polyhaven.py`,
  `render_review.py` (3x3 review sheet), `render_finals.py` (all cameras with shot_order),
  `render_cams.py` (fast GPU review renders), `peek.py` (ad-hoc viewpoint still),
  `bmcp.py` (MCP-socket fallback), `import_glb.py`, `viewport.py` (aim the user's viewport), `profile_bom.py`
  (T-slot profile totals + cut list, 20x20 / 40x40 / per collection; 2026-10-08: 693 m 20x20 incl. 171 m in 35
  chairs, 673 m 40x40; the lab has ~2.5 km 20x20 and ~1 km 40x40 in stock).
- `assets/` — CC0 textures/models/HDRI (HDRI .exr is git-ignored: `./setup.sh` re-fetches `buikslotermeerplein`
  4k exr from Poly Haven into `assets/polyhaven/hdri/`; it is the ONLY external file not in git), mural, signs.
- `.github/workflows/web-preview.yml` — PUBLIC web preview, release-only (2026-11-25): pushes to main never deploy.
  Publishing = tag `web-vN` + push the tag (or Actions -> Run workflow), only with Magnús's explicit yes per release.
  It rebuilds the site in the separate repo `MagnusPetursson/SagaModel-web` (sibling folder `../SagaModel-web`,
  `tools/publish.sh`, Blender 5.2.2 headless on GitHub Actions) and deploys it to GitHub Pages. Needs the repo secret
  `SAGA_WEB_DEPLOY_KEY`. Manual run: Actions tab → Web preview → Run workflow. No push to main triggers it.
- `PLAN.md` — the review-fix goals G1–G11 (all done). New multi-step work: write a similar plan.
- `RENDER.md` — render/video phase: final stills, presentation video script, video brand rules, pipeline, budget.
- `MACHINES.md` — machine register (see above).
- `refs/` — branding (Fab Lab Ísland brand manual 2021, signs, logos, Roboto fonts), equipment list PDF
  (the machinery list given to the architects for electrical load + airflow), user photos.
- `renders/final3/` — 29 stills at 1920x1080 (GPU OptiX, 128 spp) after G1–G11. OUTDATED (pre laser-room remodel,
  tables, print farm, craft corner): don't judge the current model from them; render fresh reviews.
  `renders/final2/` — older set (pre-G1, CPU 32 spp). `renders/tmp/` — scratch previews.

## Layout system (since 2026-11-25; details in layout/README.md)
- `layout/layout.yaml` is the ONLY source of item positions (137 items: machines, furniture, storage, fixtures). Every
  item builder ends with `apply()` (scripts/layout_blender.py): it builds at its own coordinates, then each item is
  moved so its measured footprint centre/rotation equals the yaml. Change positions in the yaml (or drag in Blender
  and snapshot), never by editing builder coordinates. An unchanged yaml is a no-op: `layout_check_identity.py`
  (0 objects changed) and `layout_check_rebuild.py` (all 16 item builders re-run: 0.0 mm / 0.0 deg) prove it.
- Companion objects (drawers, boxes, props of one builder) are parented to their item's primary, and `on:` children
  (machines on benches, props on tables) to their host, so a GUI drag of a bench carries what stands on it.
- `scripts/layout_snapshot.py`: moves + rule notes (overlap, keep-outs, walkways, zone, child left behind, locked)
  of live Blender / a .blend / another yaml against git; `--write` accepts the moves into the yaml.
- `layout/room.json` (walls, doors with swing, columns, zones, keep-outs, services, rules) comes from
  `scripts/layout_export.py`; the 2D planner on MPTVPC reads it and commits drafts to branch `layout/drafts`.
  Read `main..layout/drafts`, post the intent read-back to Magnús, polish, merge to main.
- `layout/TRUTH.md`: Magnús's answers on what the real lab is (verbatim, dated); open items stay open.
- MPDESKTOP is the only writer of the .blend. Publishing the public web preview is release-only (tag `web-vN`).

## Geometry & site facts (verified)
- Model units metres. Frame: **+Y = ESE (bearing 116°), −Y = WNW, +X = SSW (sunny façade, 206°),
  −X = NNE.** Never say north/south for plan up/down. Viewer facing −Y has +X on their LEFT.
- Scale verified: column grid 8.40 m = architects' elevation 8.398 m; width 14.99 m = OSM 15 m.
- Heights from Reykjavík drawing archive (Hagatorg 1, 2024 set by Andrúm): floor K13.00, next floor
  K17.20, concrete soffit ≈ 3.93 m clear, glazing to 3.6 m, transom ~3.30.
- Búnaðarbanki SFS secret door = a BOOKCASE door (Magnús): one 1.16 x 0.30 x 2.42 bay of the spine's shelving with
  books in the wall slot between the spine end and the demo shelving, HINGED like a normal door at its spine-side
  front corner (27.87, 36.505), swinging out 90 deg against the spine end (build_bank_walls.py). It only has to look
  convincing in the film (Magnús), not be engineered. Animated open
  in the bank shot. The birch-fin relief is gone.
- Main entrance (city drawings, Andrúm SAGA AT 20-10-02 ground-floor plan, approved 2026-06-30, USK26040333; research
  in ~/Documents/AgentWork/saga-video/hall/HALL.md): the lab includes the CORNER BAY x 32.6–34.3, y 34.7–38.3 (the
  colleague's model had it as outdoor paving + an entrance wall at x 32.63 that does not exist). The door is a single
  EI2 30 fire door in the bay's SSW wall at x 34.24–34.44, opening y 36.54–37.47, hinged ESE, opens INTO the lab (held
  open); fixed EI30 fire glass at y 35.04–36.30 beside it. It opens onto the university hall "háskóli 01-01" (same
  floor level), NOT the street. `build_entrance_bay.py` builds bay + door wall (Cut_EntranceWall boolean) and the hall
  SET for the film: glass façade along y 34.70 with an exterior double door (x 40.5–42.5), WC block x 37.0–40.1,
  y 38.67–42.6 whose two doors face the door wall off a WC lobby (end wall y 42.45), check-in desk beyond it, cleaners'
  cupboard on the door-wall side, round columns at x 44.8, stone floor, 600 acoustic ceiling at 3.10 (finishes are my
  inference from lobby photos). Hall-side signage in `build_hall_entrance.py` (fascia sign, plaque, fire-glass vinyl).
  The drawing also shows a lab escape door (pair, "ÚT") in the SSW glazing at y ~32.4–34.3 (behind the lounge pit; not
  modelled) and labels the lounge/desk area "fjölnota kennslurými 110.8 m²" (Magnús: close enough to the lounge +
  on-call area as modelled). Sun: 22 Sep 15:30 UTC (az 215°, el 22°) so light
  reaches under the ~1.9 m upper-floor overhang. HDRI rotation aligned to the sun lamp.

## Zones (current layout, user-approved)
- **Laser room** (glazed room by SSW façade, x 29.67–32.53, y 20.14–26.92; `build_laser_room.py`, collection
  LaserRoom; machine MODELS in build_machines.py, checked against the equipment list): 4.86 m profile laser bench on the
  SSW glass (flat-file sheet drawers under) with 2× Glowforge Pro HD, Glowforge Aura (orange lid), xTool F1 Ultra (UPRIGHT
  green-shield galvo tower 273x373x492 + separate touchscreen controller; checked against xTool photos) +
  1.3 m staging; Epilog Fusion Edge 24 (WHITE, navy lid band, on its white open stand; photo-checked) at the NNE/WNW corner (0.20 m off the partition, riser behind);
  laser stock rack (upright sheet slots, 0.98 m worktop, bins/rolls) on the NNE partition; 2 m standing prep counter
  under the interior window; safety station + 3 offcut bins on the WNW wall. ONE central exhaust (`Exhaust_Central`):
  rear ports → manifold behind the bench → riser (y 25.17) → ceiling collector (Epilog branch joins) → inline fan →
  up through the slab to the building's vent. Keep both doors and a ≥1.0 m aisle clear.
- **Print farm** (`build_print_farm.py`, collection PrintFarm) against the laser room's NNE partition, x 28.78–29.50,
  y 21.95–25.31: one 3.36 m profile wall, 5 bays x 3 rows of birch cells (decks 0.12/0.80/1.48/2.16) + open spool top.
  7 Prusa MK3S+ (user decision), EACH IN ITS OWN CABIN: birch sides/back, clear acrylic door hinged on the left post
  (bar handle, magnet catch), LED strip + power strip inside; one door shown open. Open cells: 3x Creality CR-200B
  (top row), Flashforge AD5M Pro (bottom row; exact Flashforge model doesn't matter), and the Bambu P2S WITH AN AMS 2 PRO
  on top in bay 0, which has no 0.80 deck (one 1.32 m cell; the AMS needs >= 0.80 m clear). Prusa 03 stands in the
  bottom row's ex-dry cell (Magnús, 2026-11-25); 2 doored dry cells. Prusa object names are fixed in PRUSA_NO.
  Real fleet: 4 MK3S + 2 MK4; the model keeps 7 MK3S+ (Magnús).
- **CNC room** (`build_cnc_room.py`, collection CNCRoom; machine models in build_machines.py): its wall to the main
  room is FLUSH WITH THE MURAL WALL (y 21.66–21.82) and is a very tall FRAMELESS glass wall (floor to slab, butt-jointed
  panes, NO aluminium frames) with a tall standard office glass door (1.0 x 2.70, glass transom, BRUSHED aluminium
  glass-to-glass hinges + pull bar, not chrome) by the NNE glass, x 20.90–21.90 (user). Sandblasted manifestation so it
  reads as glass (user): BIG frosted dots (100 mm, 200 mm apart) in single rows at 0.90 m and 1.50 m;
  the rest stays clear so the ShopBot is visible from the main room. The colleague's glazed front
  (y 23.05) is cut away (`Cut_CNC_Front`/`Cut_CNC_Side`), the strip in front is main lab. The colleague's 1.08 x 2.49 m hallway door was invented (user): replaced by a normal
  Icelandic interior door (90 x 210, frame + casings, wall completed to the slab), the knocked-down WC's doorway next
  to it walled up. ShopBot PRS Alpha 120-60 at its REAL size 3.66 x 2.31 x 1.70 (spec sheet; was 4.30 x 2.15) kept
  along the INTERIOR wall (my call; room 3.34 m wide), at x 21.74–24.05, y 17.90–21.56, ~0.9 m aisle on the glass
  side; ACword FT100 in the far glass corner; ribbed hose on a ceiling-hung swing boom (`ShopBot_DustBoom`). Operator
  corner in the ex-WC bay:
  standing PC station (control box under it, e-stop pendant) + tool bench with drawers and pegboard (bits, wrenches,
  ear defenders, glasses). Shop vac + extinguisher by the WNW wall. (Clearance ignored per user.) No SRM-20s here.
  WNW end wall (y 14.87–15.08): the 2.32 m gap (x 22.40–24.72) is a LOADING DOOR - classic double door, two
  swinging leaves (user); painted-steel leaves 2 x 1.10 x 2.40, opening outward (my details). Glass WINDOWS either
  side of it and ABOVE the door frame (user); façade-style dark frames, glazing to 3.60. Outside: concrete pavers
  (the colleague's parquet ran on outdoors).
  The back hallway's WNW end (x 26.22–27.51, an open gap in the colleague's model) is a GLASS DOOR (user): framed
  1.0 m glass leaf opening outward + narrow sidelight + fanlight, same dark frames (my details).
  The room behind the staff room (x > 27.73, door from the hallway at y 15.12–16.03) is ELECTRICAL + general storage
  (user; NOT a stairway): plain solid door, closed (`Store_Door`, build_staff_area.py); interior not modelled.
  `Cam_CNC` (from the main door), `Cam_CNCRoom` (from the operator corner).
  **Material storage** (`build_material_storage.py`): NO big sheet table; stored VERTICALLY (user, option A):
  upright board rack (2440x1220 boards on their short edge in 10 slots, slide out sideways) in the ex-WC corner against
  the hallway wall (x 24.40–25.70, y 15.15–16.70), offcut boxes/foam on its deck at 2.60 m, rods/profile on cantilever
  arms at 2.95/3.30 m; low offcut cart in the window corner; step stool. Loading door -> loading zone -> ShopBot bed in
  a straight line.
- **Microelectronics** (ESE side of the tool-wall row): tool walls refitted with drawer cabinets, tool
  rails, wire spools, multimeters; bench with **2× Roland SRM-20 (the only machines here)**, soldering
  stations + fume extractors, scope/PSU. Component storage with DRAWER units on the NNE glass
  (y 30.3–34.1). Electronics commons on the bank wall: pin-up board, whiteboard, cable pegboard, kit
  shelf, 3.2 m teaching table + 6 chairs.
- **Hand-tool wall** on the NNE glass (y 24.06–26.46; starts ≥1.0 m past the old CNC-room door line y 23.04;
  the CNC door is now at y 21.66): pegboard + shelves + counter + tool chest.
  Rule: along glass = varied tool wall + storage WITH A TABLE BELOW, not plain shelving.
- **Felt wall**: Flöff-style recycled-textile felt panels (manual orange/green/blue) on the WNW (bench)
  side of the tool walls; arched tops on the manual's 6x6 grid. NEVER a single raised rounded peak
  between lower shoulders.
- **Work tables** (`build_worktables.py`, collection WorkTables): 2x2 grid of 1.8x0.9x0.75 m profile tables (centres
  x 23.50/26.80, y 24.75/27.45), 4 profile chairs each (16), no low shelf (chairs tuck in); 1.5 m central aisle, 1.8 m
  between rows, ~1 m to the glass tool wall, 1.2 m to the print farm. Props (mats, laptops, drills) by build_life.
  The colleague's six benches + stools are gone (too dense, chairs overlapped).
- **Cutter corner** on the NNE glass: 2 Roland vinyl cutters on rolling stands (y 26.5–28.5), Cricut Maker + Mayku
  FormBox counter (y 28.55–29.55), two IKEA BEKANT carts (birch top) against felt panel 1 with the Cricut Maker 3 and
  the HANDHELD 3D scanner kit (Revopoint POP 3 stand-in: head on mini tripod, turntable, case).
- **Craft & large-format corner** (`build_textile.py`, collection Textile) between the laser room's glazed ESE
  partition (y 26.94) and the nook: 2.6 m wall bench along the partition (sit facing it, 3 chairs) with the LOKLiK
  Auto Heat Press (teal), Mug Press, overlocker, Brother embroidery + sewing, 2 EasyPress 3 on the shelf; 1.9x0.8 m
  bench on the SSW glass (x 31.65–32.45, y 28.18–30.08) with the red industrial clam press (Secabo TC7-based),
  Eazao Zero clay printer (stand-in, lab unsure; microwave + clay below) and
  Creality CR-10 Max. Main circulation x 28.0–29.5 stays clear.
- **Lounge** (by the SSW glass; `conversation_pit()` + `gullvalla()` in build_bank_lounge.py): CONVERSATION PIT - two
  IKEA GULLVALLA 2-seat sofas, one Silkeryd grey-green, one Silkeryd dark grey-beige (user's choice; real size 142 x 83 x 78, seat 42; rolled arms, two
  seat + two loose back cushions, black turned legs; modelled from IKEA photos) FACING EACH OTHER across a low birch
  coffee table (1.00 x 0.55, profile frame, shelf), at right angles to the glass (orientation was my choice); the
  glass closes one end, two felt poufs the open lab end -> a ring of 6 (idea = force interaction). Footprint
  x 30.39–32.40, y 30.11–33.29, pushed to the glass. No literal round sofa (user), no TV, no machines. RULE: the
  route from the entrance into the lab passes between the on-call desk corner (29.92, 33.87) and the pit: keep
  >= 1.2 m there (now 1.21). The pit stands in the clear zone of the SSW escape doors (y 32.4–34.3); Magnús keeps it
  there (2026-11-25: one of several exits, sofas are easily moved; the re-layouts A/B/C were all worse). Real furniture uses real catalogue dimensions. `Cam_LoungeLow` looks down the pit axis.
  `build_sofas.py` is a no-op; the old `nook()` is unused.
- **Entrance / on-call desk** (`build_welcome.py`, collection Welcome): the on-call desk is NOT a reception desk -
  one person's sitting desk (1.6 x 0.7, 0.75 m) with its BACK TO THE SPINE BOOKCASE at x 28.93–29.92, y 33.87–35.77,
  FACING THE DOOR (straight ahead) with the lounge + corridor to the lab in view; the monitor sits on the corridor
  side, screen to the sitter, so the door view is clear and visitors never see the screen. Raised birch ledge
  (1.05 m) + modesty panel on the door-facing front, wrapped round the corridor end (tent card "On call", sign-in
  tablet). RULE (user): the on-call person must face the entrance; nobody entering may see their screen.
- **Back staff area** (`build_staff_area.py`, collection StaffArea; reached by the back hallway x 25.90–27.51, which
  runs from the main lab to the WNW end). Of the two tiny WCs off the hallway, the northern one (x 24.26–25.74,
  y 17.89–19.27) was KNOCKED DOWN (user): `Cut_WC2` (Facade_Cutters, boolean on ROOT.geo0) removes its walls, its
  floor is CNC room and its hallway doorway (y 18.14–18.93) is an OPEN PASSAGE, no door (user). The other WC
  (x 24.26–25.735, y 19.42–21.66) is a standard WC (user): wall-hung toilet on a tiled cistern box, basin + mirror
  opposite the door, tiles to 1.2 m, extractor fan, door ajar, "WC" plaque. STAFF ROOM = cafeteria / meeting room /
  ranting lounge (user) in the room by the laser room (x 27.73–32.44, y 17.65–19.98 + entry bay x 27.73–29.52 to
  y 21.63, door from the hallway y 20.31–21.35). Contents per user: kitchenette (sink, fridge, coffee machine,
  microwave, dishwasher, wall cupboards), meeting table for 3–4, whiteboard (NO screen), sofa/armchair corner, coat
  hooks (NO lockers). Layout is mine: kitchen on the hallway wall with the fridge at its open end by the entry bay
  (RULE: every appliance door must open - keep >= 1 m clear in front of the whole kitchen run), table for 4 in the
  middle (end on the WNW wall), ranting corner in the window end (IKEA GLOSTAD, Knisa dark grey, on the WNW wall +
  POÄNG, Kelinge dark yellow, facing it from the laser-wall corner), whiteboard on the laser wall, coat hooks on the
  laser partition in the entry bay; ~1.1 m route along the laser wall. Signs are in ICELANDIC (user): hallway plaque
  "KAFFISTOFA / starfsfólk", "WC"; mounted flat on the wall. The laser-room wall's gap to the glass
  (x 32.15–32.52) is closed (user). `Cam_StaffRoom`.
- **Fab Lab TV**: one 85" panel wall-mounted on the spine above the desk, facing the door - the first thing you see.
  Shows a real capture of FabLabTV (github.com/FabLabReykjavik/FabLabTV, MIT) `/screen`: our print-farm render as the
  local video, Neil Gershenfeld "On Call" (user's choice: the original demo profile, he has humour for it), weather,
  clock. Re-capture: run FabLabTV (`npm start`), put a render in `videos/`, screenshot /screen at 1920x1080 after
  clicking "Start TV" -> `assets/fablabtv/fablabtv_screen.png`. No big glowing signs (user).
- **Demo display** (back-wall bays visible from the entrance, x ~27.4–32.4): imaginary Fab Lab projects,
  hex-tile art relief above. Spine's workshop side (faces electronics) = TOOL LIBRARY (`tool_library()` in
  build_microelectronics.py): cases, drills (Poly Haven Drill_01), rework/measuring gear, drawer cabinets, hand-tool
  blocks, kit boxes in the 2 visible bays; the bays behind the bank wall hold closed boxes. No demo pieces there.
- **Búnaðarbankinn** (equipment bank): STAFF ONLY, boxes only (SAMLA-style), enclosed by walls 2.80 m
  high (NOT to the slab); south wall moved to y 34.32–34.40; only entry = SECRET BOOKCASE DOOR (was: hidden in the
  birch-fin relief), y 36.46–37.71, facing the entrance. Standing desk = a niche/gap in the
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
- Colleague to confirm CNC model (list: PRS Alpha 120-60, modelled at its real 3.66 x 2.31 m; his model had a 96-60 =
  3.05 x 2.31 m; one line in build_machines.py if it is the 96-60).
- Stairwell (Magnús 2026-11-25): the windowless box x 29.2–34.3, y 12.8–16.1 at the ShopBot end is its exterior; no
  door from the lab; interior not modelled. The room behind the staff room is electrical/storage.
- Glass manifestation dots restart per pane (done 2026-11-25).
- Signs: the source PDFs' typos (VERKÆRI, ELECTRONCS) are fixed in assets/signs by `scripts/make_signs.py`, which
  re-letters them with Magnús's names (GEISLASKERI, ÞRÍVÍDDARPRENTARI, FRÆSIVÉL, RAFEINDAVERKSTÆÐI, TEXTÍLSVÆÐI,
  VERKFÆRI; VÍNYLSKERI kept). Source PDFs unchanged.
- Open from the drawings: the lab escape door in the SSW glazing (y ~32.4–34.3) where the lounge pit stands.
- Spine workshop face is 2 bays (y 31.55–34.03) + a birch end cap to the bank wall (2026-11-25); lounge face 4 bays.
- Upper hotel floors not modelled → keep exterior shots tight.
- Presentation video: plan, script, brand rules, budget in RENDER.md. `build_walkthrough.py` (shot cameras on music
  bars, one straight constant-speed move per shot, level cameras + lens shift), `render_walk_test.py` (animatic,
  ~0.15 s/frame, 640x360 Cycles), `render_walk_flat.py` (1080p flat Workbench draft via OpenGL in its own windowed
  Blender, ~0.17 s/frame, the user's preferred quick review), `make_titles.py` + `assemble_film.py` (system python3;
  brand titles, logo bug, partner outro, music, loudnorm), `render_walk_final.py` (resumable PNG sequence; NOT started
  until the user says so). Walkthrough timeline markers bind cameras:
  peek/render_cams/render_finals remove markers with cameras first, else sc.camera is overridden. The walk renderers
  switch Ground_Paving/Ground_Grass ON (hidden in the file; otherwise the HDRI ground shows as a static zoomed picture).
- Cameras reframed 2026-11-25 (`scripts/reframe_cameras.py`): Entrance, Lounge, SecretDoor; new Cam_EntranceHero
  (TV + on-call desk) and Cam_ToolLibrary (no shot_order yet: not in the finals set until Magnús picks).
- Confirmed by the lab: Epilog is 80 W; scanner is a handheld one; presses = a LOKLiK + a classic red industrial
  clam press (+ the Cricut ones); the Flashforge model doesn't matter. Still unknown (stand-ins in the model): clay
  printer (Eazao Zero; lab unsure), handheld scanner model, red press model, LOKLiK model, Brother sewing/embroidery,
  overlocker, EasyPress generation. Vinyl cutters are both Roland CAMM-1 GS-24 (confirmed).
- Prusa count: 7 now; list says 5, its power notes 10, "probably 15 printers in total".
- Finals (renders/final3) are outdated; re-render when the layout settles. New/reframed cameras: Cam_StaffRoom,
  Cam_CNC, Cam_CNCRoom, Cam_LoungeLow. Non-final cameras (Counter, Craft, Interior_01, Mural, ...) were not reframed.
- After an NVIDIA driver update the first Cycles render recompiles the OptiX kernels (~1 min); then normal again.
