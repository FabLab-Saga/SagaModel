> **Done (2026-10-07).** Superseded by CLAUDE.md for current state.

# Goal (set 2026-10-07, evening session)

Deliver a presentation-ready set of photoreal daylight renders of Fab Lab SAGA,
with every visible area fitted out in the black-profile furniture system and the
brand applied — no SketchUp placeholders left on camera.

## Work, in order
1. **Craft zone** in the workshop: purpose-built profile craft counter along the NNE
   glazing (replaces placeholder `Component_1489559`) with 2× Roland vinyl cutters on
   rolling profile stands, Cricuts, Mayku, Brother sewing + embroidery + overlocker.
2. **Spine divider** (x 27.6–28.2, y 31.5–36.7, between lounge and bank): double-sided
   profile shelving — SAMLA boxes on the bank side, books/display/plants on the lounge side.
   Remaining colleague placeholders on camera hidden (never deleted).
3. **Lighting balance**: brighten the dim WNW/mural end (pendants, bounces, exposure);
   no colour changes to brand materials (manual hex stays, tune view transform only).
4. **Equipment signs** from `refs/branding/signage` beside each machine area
   (laser, 3D printers, CNC, craft/vinyl, electronics).
5. **Cameras**: cutaway overview (ceiling hidden for that shot), entrance/lounge hero,
   workshop eye-level, laser room, print farm, mural, equipment bank.
6. **Renders**: final-quality stills (Cycles, ≥1920×1080, denoised) to `renders/final/`.

## Rules
- Everything scripted and re-runnable (`scripts/build_*.py`); commit after each step.
- Equipment bank = boxes only. Lounge/entryway (SSW glass by the entrance) = no machines.
- No single raised rounded peak between lower shoulders in any shape.
- Compass: +Y = ESE, −Y = WNW, +X = SSW, −X = NNE — never "north" for plan-up.
- Save the live Blender file after each change; never overwrite `SagaV2_work.blend`
  from the import script.

## Done when
`renders/final/` holds the 7 stills, nothing placeholder-looking is in frame, and the
work is committed. Then report back with the images and any open questions
(CNC model confirmation for the colleague is still open).
