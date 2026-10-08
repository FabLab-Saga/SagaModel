# Fab Lab SAGA — review fixes, as /goals

## Context
Review of all 35 cameras (renders/tmp/review/) found defects and weak spots. User decisions (2026-10-08):
fix leftovers, plywood colour, laser exhaust; replace the "make anything" neon with an art piece; sink exists
elsewhere (bathroom + staff cafeteria behind the laser room — drawing was outdated); design material storage;
ceiling-hung CNC dust hose; ONE central laser exhaust duct to a dedicated vent higher up the building; felt panels
stay as they are (acoustics); "ExteriorEntrance" is really the entrance from the hotel's main hall; new varied
demos; lounge → smaller circular conversation nook that keeps walkways clear; fix TV/whiteboard/books/pegboard;
raw concrete ceiling; replace pendants with office-style ceiling light arrays + occasional angled directional
spotlights.

## Rules for every goal
- Script it (new or existing builder in `scripts/`, re-runnable, rebuilds its own collection); exec in the live
  Blender via MCP; hide (never delete) colleague SketchUp objects: `for k in (o,*o.children_recursive): k.hide_render=k.hide_viewport=True`.
- Reuse `profile_furniture.py` (`Part`, `shelf_unit`, `table_unit`, `placement`, `board`, `bin_box`, `MAT`).
- Only CC0 Poly Haven or own material; record new assets in `LICENSES.md` + `assets/polyhaven/CREDITS.md`.
- Verify: GPU review renders of the affected cameras (≈5 s each) and look at them; save the .blend; update
  CLAUDE.md (build order, zones, look rules); commit + push. One goal = one commit.

## Goals (ALL DONE 2026-10-08 - commits "G1:" .. "G11:")

**G1 — Leftover cleanup.** New `scripts/cleanup_leftovers.py`: hide the colleague's 4th tool wall
`Component_1346962.003` (y≈15.3–15.8, hammers + saws, by the dust collector), the small table buried in the
component storage (`aluminum_extrusion.034–.041` + root `Plywood_4x8_Sheet_3_4_tex`, x 21.0–21.5 y 31.1–33.4),
and the bare 3 m frame `aluminum_extrusion.012–.031` (x 27.2–28.0, y 29.8–30.6) if it isn't load-bearing for
anything kept. Done when CompStorage, SewingDetail and CNCRoom renders show no strays.

**G2 — Materials: pale birch + raw concrete ceiling.** In `apply_pbr.py`/`detail_materials.py`: make
`Plywood_Birch` read as pale birch (currently apply_pbr.py:173 swaps the procedural `birch_ply()` for the Poly Haven `plywood` scan) (#E0C9A2-ish: a CC0 birch-ply texture, or hue/value-correct the current one;
keep the grain). The ceiling is most likely `Concrete_Exposed` = Poly Haven `concrete_slab_wall` (apply_pbr.py:170; triplanar, 2.3 m tile), which renders like timber boards — check the slab's actual material in the .blend first, then replace it with a CC0 Poly Haven raw/cast concrete texture, box-mapped at
real scale, with subtle formwork joints and no wood character. Done when Counter, Craft, Micro and Entrance read
pale birch, and every interior ceiling reads as raw concrete.

**G3 — Neon sign → art piece.** Remove `Demo_NeonSign`, `Demo_NeonBacking` and the Neon_Pink accents
(demo + spine). Replace them above the demo bays (x 29.1–31.8, z 2.6–3.3) with a large lab-made wall art piece
(e.g. a layered laser-cut/CNC-milled relief or a parametric slat sculpture in brand colours), lit by one
directional spot. Done when Demo, Counter and SecretDoor renders show the piece and no pink spill.

**G4 — Central laser exhaust.** Rewrite the laser-room exhaust in `build_machines.py`: short flexible hose from
each machine's REAR port (low on the back) into one galvanised collector duct running along the room high under
the slab, then one inline fan, then a single exit up to the building's dedicated vent higher up (riser on the
façade/through the beam). The Epilog joins the same duct. No vertical pipes in front of the glazing. Done when
LaserRoom and LaserDetail show a clean single-duct system.

**G5 — Material storage.** Design + build `scripts/build_material_storage.py`: vertical sheet rack for
1220×2440 sheets (ply/MDF/acrylic, stood on edge, profile + ply), offcut bins, and a rod/profile rack, in
40x40 profile language. Default location: the freed CNC-room end by the glass (y≈15.3–16.2, beside the
dust collector), near the ShopBot; fall back to another spot if it doesn't fit. Done when it's visible in the
CNC shots and fits without collisions.

**G6 — CNC dust hose.** Replace `ShopBot_DustHose` (stiff arch) with a ceiling-hung swing boom/trolley and
ribbed flexible hose drooping to a brush dust skirt on the spindle, then to the collector inlet (21.50, 16.72,
1.12). Done when CNC, CNCRoom and ShopBot read as a real install.

**G7 — New demo pieces.** Extend `build_demo.py` with more varied, larger projects (e.g. CNC-cut chair or
stool, kerf-bent lamp, 3D-printed lattice vase, laser-cut map relief, PCB synth/badges with a stand, textile
piece, wooden mechanism/automaton) plus small labels. No visible repeats within a bay; fewer, bigger hero
pieces at eye level. Done when Demo and the spine's workshop side look curated.

**G8 — Lounge overhaul.** Rebuild the lounge (`build_bank_lounge.py` + `build_sofas.py`) as a smaller,
intimate, CIRCULAR conversation nook (curved modular seating or sofa + chairs around a round low table,
≈3–3.5 m across) by the SSW glass. Keep a clear ≥1.2 m path from the entrance (y 35.1–36.2) into the lab and
along the glass. Re-place or drop the TV and poufs as fits. Update Cam_Lounge, Cam_LoungeLow, Cam_Entrance and
Cam_Counter framing. Done when the nook reads as one circle and the walkways are clear in the Cutaway.

**G9 — Props, plus the hall entrance.**
- TV screen: an emissive Fab Lab slide.
- Whiteboard: a real circuit diagram or class plan instead of random dashes.
- Books: varied spines with title bands.
- Hand-tool pegboard: fill it out properly; resize the oversized yellow cable reel.
- Rename `Cam_ExteriorEntrance` → `Cam_HallEntrance`, record in CLAUDE.md that this is the entrance from the
  hotel's main hall, and give it Fab Lab signage/branding on the hall side.

Done when the affected shots look lived-in.

**G10 — Lighting overhaul.** Remove every round pendant (`pendants()`/`pendant_points()` in build_services.py: Pendant_* meshes + POINT lights `Pendant_Light_NN`, 180 W). Add office-style ceiling light arrays
(suspended linear LED or panel grid over work zones, aligned to the column grid and clear of ducts and trays
in `build_services.py`: main duct x 25.9 (z 3.40–3.85), branch x 30.6 (y≥27.4), trays x 23.2/29.0 (bottom ≈3.31), sprinklers x 22.0/28.4/31.7), plus occasional angled ceiling-mounted directional spotlights on the mural, demo/art
piece, felt wall and lounge. Real light objects with sensible lumen-like strengths. Re-balance per-camera
`exposure_offset`. Done when all shots are evenly lit, with no fixtures cutting through frames (HighCorner,
MuralFront).

**G11 — Final pass.** Render all 35 cameras for review, fix regressions, rerun `render_finals.py`
into `renders/final3/`, update CLAUDE.md open items, commit + push.

## Verification (each goal)
`blender -b SagaV2_work.blend --python <scratch all_cams.py>` (GPU, 1280x720, 32 spp) → read the renders →
`git commit && git push`.
