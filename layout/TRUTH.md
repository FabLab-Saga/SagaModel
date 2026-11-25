# Fab Lab SAGA: truth sheet

What the real lab is or will be, for the layout work. Every answer is Magnús's, quoted with its date. Anything not
answered stays **open**; the model keeps its current stand-in until then. Talos keeps this file current.

Sources on record: Andrúm SAGA AT 20-10-02 ground-floor plan (city drawing archive, approved 2026-06-30,
USK26040333); Hagatorg 1 2024 set (heights); the equipment list "Tæki og búnaður í Mixtúru og FabLabVON"
(`refs/equipment/`); Magnús's photos from July 2026 (`refs/images/`); his decisions of 2026-10-08 (PLAN.md);
MACHINES.md. Nothing newer is on MPDESKTOP as of 2026-11-25.

Questions sent 2026-11-25 ~13:40 UTC (relayed via Hermes on MPTVPC; the Bot Chat run could not prompt him directly).

| # | Topic | Model now | Magnús (date, verbatim) | Status |
|---|---|---|---|---|
| 1 | Escape door (pair, ÚT) in the SSW glazing, y ≈ 32.4–34.3 | Not modelled; the lounge pit stands there. room.json has it as `escape-ssw-1/2` from the drawing | | open |
| 2 | Stairwell location | Unknown; the room behind the staff room is electrical/storage (Magnús, earlier) | | open |
| 3 | ShopBot model | PRS Alpha 120-60, 3.66 × 2.31 m (equipment list); colleague's model had a 96-60 (3.05 × 2.31 m) | | open |
| 4 | Prusa count | 7 MK3S+ (Magnús, 2026-10-08); list says 5, its power notes 10, "probably 15 in total" | | open |
| 5 | Stand-in machine models | Clay printer (Eazao Zero), handheld scanner (Revopoint POP 3), red clam press (Secabo TC7), LOKLiK press, Brother sewing (CS7000X) + embroidery (PE900), overlocker (Brother 1034D), EasyPress generation | | open |
| 6 | Spine bays 0–1 face the bank wall 5 cm away | Closed boxes only | | open (offer: shorten the spine) |
| 7 | Glass manifestation dots run straight across pane joints | Continuous pattern | | open (offer: restart per pane) |
| 8 | Stale cameras (Entrance, Lounge, SecretDoor; no tool-library camera) | Old framing | | open (reframe after the layout settles) |
| 9 | Anything newer than the June 2026 Andrúm plan (furniture plan, drawings, photos) | None on MPDESKTOP | | open |
| 10 | SagaModel-web "Site code" workflow still deploys `site/**` pushes publicly | Unchanged | | open (offer: release-only too) |

Confirmed earlier (from CLAUDE.md, for reference): Epilog is 80 W; the scanner is handheld; presses = a LOKLiK + a
red industrial clam press (+ the Cricut ones); the Flashforge model doesn't matter; both vinyl cutters are Roland
CAMM-1 GS-24; the room behind the staff room is electrical + general storage, not a stairway; the corner bay
x 32.6–34.3, y 34.7–38.3 belongs to the lab and the entrance is the EI2 30 fire door from the university hall.
