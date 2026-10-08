# Logo sources: Fab Lab SAGA video outro

Collected 2026-10-08. Every file was rendered and checked by eye on black and on white (`contact.png`).
Raw downloads and intermediate files are in `_raw/`.

Legend:
- **OFFICIAL**: the organisation's own file, unchanged.
- **CONVERTED**: an official file converted to another format with no visual change (PDF→SVG with Inkscape, text outlined).
- **DERIVED**: an official artwork recoloured or cropped by us. It is not a file the organisation publishes.
- **FALLBACK**: taken from the local poster `SagaModel/refs/branding/Poster_FabLabSaga_A4.svg`.

---

## 1. Háskóli Íslands – Verkfræði- og náttúruvísindasvið (Icelandic)

Source page (official HÍ design standard, "Hönnunarstaðall HÍ" → Myndmerki HÍ → *Auðkenni sviða, deilda og stofnana* → tab *Verkfræði- og náttúruvísindasvið*):
https://honnun.hi.is/5afb7ec03/p/191b65-myndmerki-hi/b/612d94
The download links are S3 URLs that expire after 5 minutes, so the original file names are given instead: `hi-audkenni_25-verknatt.pdf` / `.png` (dated 27 Sep 2021). The `_en` files are the English versions and are not used here.

| File | Status | Format | Size |
|---|---|---|---|
| `HI_Verkfraedi-og-natturuvisindasvid_IS_blue_official.pdf` | OFFICIAL | PDF (vector, InDesign, Jost-Medium embedded) | page 1100×130 pt, art ≈1153×113 pt |
| `HI_Verkfraedi-og-natturuvisindasvid_IS_blue_official.png` | OFFICIAL | PNG RGBA, transparent | 2292×271 px |
| `HI_Verkfraedi-og-natturuvisindasvid_IS_blue.svg` | CONVERTED from the official PDF (colour set to the HÍ screen blue #10099F, as used in HÍ's own SVGs; the PDF uses CMYK ≈ #0803A3) | SVG vector | 1152.6×112.7 |
| `HI_Verkfraedi-og-natturuvisindasvid_IS_white.svg` | DERIVED (the same SVG, all fills #FFFFFF; the Athena seal lines remain transparent knock-outs) | SVG vector | 1152.6×112.7 |
| `..._white_1000h.png`, `..._blue_1000h.png` | renders of the SVGs | PNG RGBA | 10226×1000 px |

Colour variants published for this school: **blue only** (IS + EN, PDF + PNG). HÍ does not publish a white school identifier. The white master HÍ logos (`haskoli_isl_hvitt_*.svg/pdf`, in `_raw/hi/`) do not include the school name.

## 2. Háskóli Íslands – Menntavísindasvið (Icelandic)

Same page as above, tab *Menntavísindasvið*: https://honnun.hi.is/5afb7ec03/p/191b65-myndmerki-hi/b/612d94
Original files: `hi-audkenni_20-mvs.pdf` / `.png` (27 Sep 2021).

| File | Status | Format | Size |
|---|---|---|---|
| `HI_Menntavisindasvid_IS_blue_official.pdf` | OFFICIAL | PDF vector | page 1100×130 pt, art ≈770×113 pt |
| `HI_Menntavisindasvid_IS_blue_official.png` | OFFICIAL | PNG RGBA, transparent | 2292×271 px |
| `HI_Menntavisindasvid_IS_blue.svg` | CONVERTED from the official PDF (#10099F) | SVG vector | 770.5×112.7 |
| `HI_Menntavisindasvid_IS_white.svg` | DERIVED (all fills white) | SVG vector | 770.5×112.7 |
| `..._white_1000h.png`, `..._blue_1000h.png` | renders | PNG RGBA | 6836×1000 px |

Colour variants published: **blue only**. There is no official white version of the school identifier.

### HÍ rules (from honnun.hi.is, Myndmerki HÍ + *Notkunarreglur*)
- "Merki skólans eru að stofni til einungis **fagurblá eða hvít** og skipta ekki lengur litum eftir fræðasviðum." (The logos are only bright blue or white, with no faculty colours.) White is therefore an allowed colour, so a white identifier for white-on-black use stays within the standard. The white school identifier itself is our recolour, not an HÍ file.
- Units never have their own logos. The school identifier is the HÍ logo plus the unit name, as shown in the standard. Units may not use any logo other than those in the standard, or use them in any other way.
- Who may use the logo: permanent staff, schools, faculties and institutes. The identifier may also be used "ásamt auðkennum annarra aðila, ef fyrir hendi er samstarfssamningur um tiltekin verkefni … Einnig ef um er að ræða sameiginleg verkefni" (alongside other parties' logos when there is a cooperation agreement or a joint project). Fab Lab SAGA is a joint HÍ project, so this applies. Keep the Jost typeface, which is already embedded in the files.
- Seal-text Pallas Athena + school name is mandatory on formal documents. This does not apply to a video outro.
- Wikipedia's copy of the logo notes that it is a registered trademark of Háskóli Íslands.

---

## 3. Reykjavíkurborg: shield + "Reykjavík" wordmark

Official sources:
- Web-ready SVGs on the city's style server, linked from Hanna (Merki → *Code*: https://hanna.reykjavik.is/7be457c46/p/0676b1-merki/b/465a6b):
  https://styles.reykjavik.is/assets/reykjavik-logo.svg and https://styles.reykjavik.is/assets/reykjavik-logo-notext.svg
- Hanna, Merki → *Logo* (sections Blátt / Hvítt / Skjaldarmerki): https://hanna.reykjavik.is/7be457c46/p/0676b1-merki/b/71a246
- White shield SVG used on https://reykjavik.is/mixtura: https://reykjavik.is/sites/default/files/2026-09/white.svg
- Brand guide: https://reykjavik.is/sites/default/files/2023-03/Vorumerkjahandbok_Reykjavikur.pdf (linked from https://reykjavik.is/midlun)

| File | Status | Format | Size |
|---|---|---|---|
| `Reykjavik_logo_colour.svg` | CONVERTED from reykjavik-logo.svg: CSS variables resolved (shield #0376E1, text #3D3F3E), white backing shape removed so gaps are transparent, as in Hanna's PNGs | SVG vector | viewBox 579.9×168.4 |
| `Reykjavik_logo_white.svg` | DERIVED from the official SVG, all white. Same artwork as the official Hanna "Hvítt" PNG | SVG vector | 579.9×168.4 |
| `Reykjavik_logo_black.svg` | DERIVED, all black | SVG vector | 579.9×168.4 |
| `Reykjavik_skjaldarmerki_colour.svg` / `_white.svg` / `_black.svg` | CONVERTED/DERIVED from reykjavik-logo-notext.svg (shield only) | SVG vector | — |
| `Reykjavik_skjaldarmerki_white_reykjavik-is.svg` | OFFICIAL white shield (from reykjavik.is) | SVG vector | 104×162 |
| `Reykjavik_logo_colour_hanna.png` | OFFICIAL (Hanna "Blátt") | PNG RGBA | 1153×324 px |
| `Reykjavik_logo_white_hanna.png` | OFFICIAL (Hanna "Hvítt") | PNG RGBA | 1153×324 px |
| `Reykjavik_skjaldarmerki_colour_hanna.png` / `_white_hanna.png` | OFFICIAL (Hanna "Skjaldarmerki") | PNG RGBA | 207×324 px |
| `Reykjavik_logo_{colour,white,black}_1000h.png`, `Reykjavik_skjaldarmerki_white_1000h.png` | renders of the SVGs | PNG RGBA | 3557×1000 / 639×1000 px |
| `Vorumerkjahandbok_Reykjavikur.pdf` | OFFICIAL brand guide (v1.0, March 2023, 34 pp) | PDF | — |

Colour variants found: **full colour** (blue shield + dark-grey wordmark; the brand guide prints the wordmark near-black), **white** (official PNG + white shield SVG), **black** (shown in the guide). The wordmark is the Reykjavík lettering, already outlined in the SVG.

### Reykjavík rules (Vörumerkjahandbók pp. 2, 5–6, 29–33; Hanna)
- The logo is the shield plus "Reykjavík" in the correct typeface. "Reykjavíkurborg" is used in running text only.
- "**Merki má notast einlit svart eða hvítt**" (the logo may be used in one colour, black or white).
- "**Á flóknum bakgrunni skal nota merkið hvítt á bláu eða svörtu**" (on complex backgrounds use the logo white on blue or black). White on black is explicitly approved.
- Don't recolour part of the logo, don't tilt it, don't move or squeeze its parts, and don't put it in a box.
- The general rule is shield + Reykjavík together; the shield alone is allowed when that isn't possible.
- Keep at least one shield-width between the Reykjavík logo and the next logo. Minimum shield height is 5 mm in print.
- Sponsorship/partnership (p. 31): "skal ávallt notast við skjaldarmerki ásamt Reykjavík … Ekki skal auðkenna hvaða sviði eða undirstofnun verkefnið tilheyrir nema rík ástæða teljist til". In partnerships, use shield + Reykjavík and don't name the department or sub-unit without good reason. This matters for showing Mixtúra separately.
- Hanna (for web): link to the style-server files rather than hosting copies. Not relevant for video.
- No licence or copyright text is given beyond these rules. The coat of arms is a registered municipal emblem (byggðarmerki).

---

## 4. Mixtúra (sköpunar- og tækniver skóla- og frístundasviðs Reykjavíkur)

The current official page https://reykjavik.is/mixtura (mixtura.is now redirects there) shows **no Mixtúra logo**, only the Reykjavík logo. That fits the Reykjavík brand guide's rule of branding sub-units under Reykjavík. The logo below is from the archived official site mixtura.is (WordPress uploads), retrieved via the Wayback Machine:
- https://web.archive.org/web/20211001232720id_/http://mixtura.is/wp-content/uploads/2021/03/logo.png (original URL `http://mixtura.is/wp-content/uploads/2021/03/logo.png`)
- A smaller site-header version `2021/12/Untitled-design-3.png` (300×90, with the Reykjavík shield) is in `_raw/mixtura/`.

| File | Status | Format | Size |
|---|---|---|---|
| `Mixtura_logo_colour_mixtura-is-2021.png` | OFFICIAL artwork from Mixtúra's own former site, via the archive | PNG RGBA (red #DC1F26 tiles, letters knocked out = transparent) | 2099×645 px |
| `Mixtura_logo_white_derived.png` | DERIVED: every opaque pixel set to white (white tiles, transparent letters, white tagline) | PNG RGBA | 2099×645 px |
| `Mixtura_wordmark_colour_derived-crop.png` / `Mixtura_wordmark_white_derived-crop.png` | DERIVED: wordmark only, without the old tagline | PNG RGBA | 2049×413 px |
| `Mixtura_logo_poster-fallback_542px.png` | FALLBACK: extracted from the local poster. Opaque (red tiles, black letters and band), low resolution. Same design; not recommended | PNG | 542×109 px |

Colour variants found: **red only**. There is no white or black version and no vector file anywhere public.
- The tagline in the 2021 file reads "SKÖPUNAR- & UPPLÝSINGATÆKNIVER SFS", the **old name**. The current name is "sköpunar- og tækniver". For the outro, use the wordmark-only crop.
- No usage terms are stated anywhere.

---

## Gaps / to confirm
1. **HÍ school identifiers**: there is no official white file. The white SVGs are exact recolours of the official vector PDFs, and the HÍ standard allows white. If needed, confirm with HÍ Markaðs- og samskiptasvið.
2. **Mixtúra**: no vector, no white version, and no logo on the current official page. The best source is the 2021 PNG from the archived mixtura.is. Ask Mixtúra (mixtura@reykjavik.is) for a current vector/white file and whether they still use their own logo. Under the Reykjavík brand rules they might prefer to be credited as "Reykjavík" (shield + wordmark) with "Mixtúra" in text.
3. Reykjavík wordmark colour: the web SVG uses dark grey #3D3F3E and the print guide near-black. Irrelevant for the white outro.
4. Comparison with the local poster: the poster uses the same HÍ school identifiers, Reykjavík logo and Mixtúra tile wordmark as found here. Only the Mixtúra file was taken from it, as a fallback.
