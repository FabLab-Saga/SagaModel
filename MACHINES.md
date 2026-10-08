# Machines: equipment list vs the Blender model

Checked 2026-10-08 against `refs/equipment/Tæki og búnaður í mixtúru og FabLabVON - Tæki og búnaður.pdf`
(Mixtúra smiðja + FabLab VoN columns; "Búnaðarbankinn" items are stored in boxes) and the live `SagaV2_work.blend`
(visible objects only). Images: manufacturer/retailer product shots, each URL checked to return HTTP 200 image/*.
Dimensions W x D x H mm from the manufacturer unless noted.

Status: OK = model count matches the list. MORE = more copies in the model than listed. MISSING = listed, not modelled.

## In the model

| Machine (exact model) | List qty | Model qty | Status | Blender objects | Zone | Image | Product page | Dims (mm) | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Glowforge Pro HD (45 W CO2, pass-through) | 2 (Mixtúra) | 2 | OK | `Glowforge_ProHD_1`, `_2` | Laser room bench | [img](https://shop.glowforge.com/cdn/shop/files/GF-Pro_HD-Front_1_grande.png?v=1751386674) | [glowforge.com](https://shop.glowforge.com/products/glowforge-pro-hd) | 965 x 527 x 210 | List: 965 x 527 x 211 |
| Glowforge Aura (6 W diode) | 1 (Mixtúra) | 1 | OK | `Glowforge_Aura` | Laser room bench | [img](https://shop.glowforge.com/cdn/shop/files/Aura-02_683d825b-9a79-49bc-8bd6-f4258d79437f_grande.jpg?v=1763677928) | [glowforge.com](https://shop.glowforge.com/products/glowforge-aura) | 556 x 521 x 127 | Image is a top view |
| Epilog Fusion Edge 24 | 1 (VoN) | 1 | OK | `Epilog_FusionEdge24` | Laser room corner, own stand | [img](https://www.epiloglaser.com/assets/img/fusion-edge_series.webp) | [epiloglaser.com](https://www.epiloglaser.com/laser-machines/fusion-edge-laser-cutter-engraver/) | list: 1055 x 834 x 967 (likely incl. stand) | Image shows the 12/24/36 range together. List says 80 W; Epilog currently sells the 24 in 50/60 W - confirm |
| xTool F1 Ultra (20 W fibre + 20 W diode galvo) | 1 (VoN, qty blank) | 1 | OK | `xTool_F1_Ultra` (+ `_Controller`) | Laser room bench | [img](https://www.xtool.com/cdn/shop/files/mk-baidituyingyong_au_pc_en-f1ultra-whitebackground_5144-593.webp?v=1747646544) | [xtool.com](https://www.xtool.com/products/xtool-f1-ultra-20w-fiber-diode-dual-laser-engraver) | 493 x 253 x 373 (stands upright: 493 = height) | Quantity cell empty in the list; read as 1 |
| ShopBot PRSalpha 120-60 (now sold as PRS5 Alpha) | 1 (VoN) | 1 | OK | `ShopBot_PRSAlpha_120` | CNC room | [img](https://i0.wp.com/shopbottools.com/wp-content/uploads/2024/06/PRS5_Alpha_1080wide_JUN2024.jpg?w=1076&ssl=1) | [shopbottools.com](https://shopbottools.com/products/shopbot-prs5-alpha/) | 3050 x 2310 x 1700 (L x W x H) | Colleague's model had a 96-60 (same footprint) - still to confirm |
| ACword FT 100 dust collector | 1 (VoN, "ACword FT100 Ryksafnari fyrir ShopBot Fræsi") | 1 | OK | `ACword_FT100` | CNC room glass corner | [img](https://idnvelar.is/wp-content/uploads/2018/01/ft100.jpg) | [elbh.cz](https://www.elbh.cz/odsavac-pilin-ft-100.php) | 840 x 500 x 2200 | Real brand (Czech, now ELBH s.r.o.); sold in Iceland by Iðnvélar. Specs match the list exactly |
| Original Prusa i3 MK3S+ | 5 (VoN) | **12** | **MORE** | `Prusa_MK3S_01` .. `_12` | Print farm | [img](https://www.prusa3d.com/content/images/product/226b1536-4128-44d9-9c7c-50c4a8697957.jpg) | [prusa3d.com](https://www.prusa3d.com/product/original-prusa-i3-mk3s-3d-printer-3/) | 500 x 550 x 400 | List qty 5, but its power notes plan "10 x Prusa" and "at least 10 printers in total, probably 15". Decide 5 / 10 / 15 |
| Bambu Lab P2S | 1 (Mixtúra) | 1 | OK | `Bambu_P2S` | Print farm top | [img](https://store.bblcdn.com/s7/default/8b5e77334d6d4e358ca739e6ab9dbd84/P2S-compressed.jpg) | [bambulab.com](https://bambulab.com/en/p2s) | 392 x 406 x 478 | Needs ~80 cm headroom with AMS 2 Pro on top (list note) |
| Roland DG monoFab SRM-20 | 2 (1 Mixtúra + 1 VoN) | 2 | OK | `Roland_SRM20_1`, `_2` | Microelectronics bench | [img](https://image.rolanddg.com/-/media/roland-apac/mea/images/products/3d/srm20/overview/srm20overviewmobile.jpg?rev=4cf2979acdf84e5e8567b680d8ca69a6) | [rolanddg.com](https://global.rolanddg.com/products/milling-machines/srm-20-compact-milling-machine) | 451 x 426.6 x 426.2 | One per lab, both listed |
| Roland desktop vinyl cutter (GS2-24 or older CAMM-1 GS-24) | 2 (1 Mixtúra + 1 VoN) | 2 | OK | `Roland_VinylCutter_1`, `_2` | Cutter corner, NNE glass | [img](https://image.rolanddga.com/-/media/roland/images/products/cutters/gs224/gs2-24-og.jpg?rev=57fec05808cd41a4aa000c0228f4374e) | [rolanddga.com](https://www.rolanddga.com/products/vinyl-cutters/versastudio-gs2-24-desktop-vinyl-cutter) | 860 x 319 x 235 | Roland gives the same size for GS-24 and GS2-24; check the model plates. GS-24: [img](https://cdn.rolanddg.eu/-/media/roland-emea/images/products/cutters/gs24/overview/gs24standwide.jpg) |
| Cricut Maker (1st gen) | 1 (Mixtúra) | 1 | OK | `Cricut_Maker_1` | Cutter counter, NNE glass | [img](https://cricut.com/on/demandware.static/-/Sites-cricut-master-catalog/default/dw8e9780f4/images//2/0/2003925-3_7.jpg) | [cricut.com (refurb page; discontinued)](https://cricut.com/en-us/sale/refurbished-open-box-machines/certified-refurbished-cricut-maker/2009174.html) | 584 x 178 x 156 | |
| Mayku FormBox vacuum former | 1 (Mixtúra) + 2 in the bank | 1 | OK | `Mayku_FormBox` | Cutter counter, NNE glass | [img](https://d1ds8nu9vo9fn9.cloudfront.net/images/_1200x630_crop_center-center_82_none/formbox-included.jpg?mtime=1786713540) | [mayku.me](https://mayku.me/formbox) | 466 x 274 x 315 | The 2 in the bank are boxed |
| Brother computerised sewing machine (model unknown; stand-in CS7000X) | 1 (Mixtúra) | 1 | OK | `Brother_Sewing` | Textile, SSW glass | [img](https://assets.brother.com/transform/ba532861-089b-41b7-ae0d-3216081d3a15/13524_CS7000X_WT_FRONT_1128x846-png?io=transform:fit,width:1600) | [brother-usa.com](https://www.brother-usa.com/p/sewing/CS7000X) | 413 x 169 x 310 | Actual model to confirm |
| Brother embroidery machine (model unknown; stand-in PE900) | 1 (listed under the bank) | 1 | OK | `Brother_Embroidery` | Textile, SSW glass | [img](https://assets.brother.com/transform/196e4ce9-13f4-4da9-baed-869a4b4448f1/18489_20_PE900_front_w-png?io=transform:fit,width:1600) | [brother-usa.com](https://www.brother-usa.com/p/embroidery/PE900) | 241 x 444 x 300 | Listed in the bank section; modelled out on the sewing table |
| Overlocker (brand unknown; stand-in Brother 1034D) | 1 (Mixtúra) | 1 | OK | `Overlock` | Textile, SSW glass | [img](https://assets.brother.com/transform/36876837-4e8d-467a-8762-35a6f2d81030/3466_1034D_front-png?io=transform:fit,width:1600) | [brother-usa.com](https://www.brother-usa.com/p/sergers-coverstitch/1034D) | 298 x 279 x 335 | Actual model to confirm |

Every machine above exists exactly once per listed unit (no duplicate objects); the only count mismatch is the Prusa farm.

## Listed but not in the model

| Machine | List qty | Image | Product page | Dims (mm) | Notes |
|---|---|---|---|---|---|
| Creality CR-10 Max | 1 (VoN) | [img](https://img.matterhackers.com/g/Z3M6Ly9taC1wcm9kdWN0LWltYWdlcy9wcm9kL2JmYzhmMDQ5LTA4ZmQtNDM0YS1hNzg4LWE4YTljOGUyMGQwZQ=e365-w1200-h630-c0xffffff-rj-pd) | [matterhackers.com](https://www.matterhackers.com/store/l/creality3d-cr-10-max-3d-printer/sk/MJPWRVVL) (Creality page gone; discontinued) | 650 x 785 x 735 | Big open-frame printer; doesn't fit the 0.58 m shelf pitch |
| Creality 3D printers | 3 (Mixtúra) | - | - | list: 411 x 435 x 503 | Model not given (the same size is pasted on the Flashforge and clay-printer rows) |
| Flashforge 3D printer | 1 (Mixtúra) | - | - | - | Model not given |
| Clay 3D printer | 1 (Mixtúra) | - | - | - | Model not given; note: "clay, microwave, accessories" |
| 3D scanner | 1 (Mixtúra) | - | - | - | Model not given |
| Cricut Maker 3 | 1 (Mixtúra) + "Cricut machines 5" in bags in the bank | [img](https://cricut.com/on/demandware.static/-/Sites-cricut-master-catalog/default/dwdca6c769/PDPMVP/1_DTC_Hero_2008335.jpg) | [cricut.com](https://cricut.com/en/cutting-machines/cricut-maker-3/2008335.html) | 538 x 178 x 151 | The 5 in bags would be boxed in the bank |
| Large black heat press | 1 (Mixtúra) | - | - | - | Model not given |
| Cricut EasyPress (generation unknown; stand-in EasyPress 3 12x10") | 2 (Mixtúra) | [img](https://cricut.com/on/demandware.static/-/Sites-cricut-master-catalog/default/dw1d3c969a/Misc./01_2009150_hero.png) | [cricut.com](https://cricut.com/en-gb/heat-presses/easypress-machines/easypress-12-x-10/cricut-easypress-3---12-x-10/2009151.html) | plate 305 x 254 | |
| Cricut Mug Press | 1 (Mixtúra) | [img](https://cricut.com/on/demandware.static/-/Sites-cricut-master-catalog/default/dwd83ed1bd/Misc./2008736-2.png) | [cricut.com](https://cricut.com/en/heat-presses/mug-press/cricut-mug-press/2008736.html) | 275 x 157 x 165 | |

Also on the list, not machines: podcast sets 2, photo sets 2, sound systems 3 (bank, in cases); furniture: IKEA Bekant
carts 5 large + 4 small, Bror carts 2, Cleveland sofas (3-seat x2, 2-seat x1; retired from the model), TV screens on
wheels 2 (80-90"), vertical info screens 2, 5 black electric sit-stand tables (120/200/200/200/250 x 60 cm,
h 80-100; suggested for the laser room or a meeting room). Not modelled.

Not on the list but in the model: soldering stations x3, fume extractors x3, oscilloscope/PSU sets, cordless drills
(Poly Haven CC0 asset), hand tools - electronics/tool-library kit.
