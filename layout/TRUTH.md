# Fab Lab SAGA: truth sheet

What the real lab is or will be, for the layout work. Every answer is Magnús's, quoted with its date. Anything not
answered stays **open**; the model keeps its current stand-in until then. Talos keeps this file current.

Sources on record: Andrúm SAGA AT 20-10-02 ground-floor plan (city drawing archive, approved 2026-06-30,
USK26040333); Hagatorg 1 2024 set (heights); the equipment list "Tæki og búnaður í Mixtúru og FabLabVON"
(`refs/equipment/`); Magnús's photos from July 2026 (`refs/images/`); his decisions of 2026-10-08 (PLAN.md);
MACHINES.md. Nothing newer is on MPDESKTOP as of 2026-11-25.

Questions sent 2026-11-25 ~13:40 UTC (relayed via Hermes on MPTVPC; the Bot Chat run could not prompt him directly).
Q1–4 and 9 are with him in #hermes-control (answers pending).

| # | Topic | Model now | Magnús (date, verbatim) | Status |
|---|---|---|---|---|
| 1 | Escape door (pair, ÚT) in the SSW glazing, y ≈ 32.4–34.3 | Not modelled; the lounge pit stands there. room.json has it as `escape-ssw-1/2` from the drawing | | open |
| 2 | Stairwell location | Unknown; the room behind the staff room is electrical/storage (Magnús, earlier) | | open |
| 3 | ShopBot model | PRS Alpha 120-60, 3.66 × 2.31 m (equipment list); colleague's model had a 96-60 (3.05 × 2.31 m) | | open |
| 4 | Prusa count | 7 MK3S+ (Magnús, 2026-10-08); list says 5, its power notes 10, "probably 15 in total" | | open |
| 5 | Stand-in machine models | Clay printer (Eazao Zero), handheld scanner (Revopoint POP 3), red clam press (Secabo TC7), LOKLiK press, Brother sewing (CS7000X) + embroidery (PE900), overlocker (Brother 1034D), EasyPress generation | | open |
| 6 | Spine bays 0–1 faced the bank wall 5 cm away | Done 2026-11-25: workshop face cut to the 2 bays facing the room (y 31.55–34.03, contents unchanged), birch end cap closes the slot to the bank wall; lounge face (4 bays, TV, secret door) unchanged. The workshop-face-only cut and the end cap are my choices | "Go on all. paralellize." (2026-11-25, via Hermes: (a)-(c) are polish inside the approved plan) | done |
| 7 | Glass manifestation dots ran straight across pane joints | Done 2026-11-25: dots restart on every pane (whole dots, centred, ≥ 80 mm from the edges); the 9 cm sliver pane next to the façade now has none | same | done |
| 8 | Stale cameras | Done 2026-11-25 (`scripts/reframe_cameras.py`, my framings): Entrance, Lounge, SecretDoor reframed; new Cam_EntranceHero (TV + on-call desk) and Cam_ToolLibrary | same | done; re-check after Magnús's layout moves |
| 9 | Anything newer than the June 2026 Andrúm plan (furniture plan, drawings, photos) | None on MPDESKTOP | | open |
| 10 | SagaModel-web "Site code" workflow deployed `site/**` pushes publicly | Done 2026-11-25: release-only (SagaModel-web f1ae0d0) | "Make sure Talos' point of the builds and deploys is fixed." (2026-11-25, via Hermes: no push of any kind publishes; only a web-v* tag or manual run, no tag without his yes) | done |

Confirmed earlier (from CLAUDE.md, for reference): Epilog is 80 W; the scanner is handheld; presses = a LOKLiK + a
red industrial clam press (+ the Cricut ones); the Flashforge model doesn't matter; both vinyl cutters are Roland
CAMM-1 GS-24; the room behind the staff room is electrical + general storage, not a stairway; the corner bay
x 32.6–34.3, y 34.7–38.3 belongs to the lab and the entrance is the EI2 30 fire door from the university hall.
