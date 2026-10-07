// Rasterise an SVG (e.g. assets/mural/mural.svg) at 1 px per unit: node rasterize_svg.mjs <abs.svg> <out.png> [scale]
import puppeteer from 'puppeteer-core';
const [svg, png, scale] = process.argv.slice(2);
const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new', args: ['--allow-file-access-from-files'] });
const p = await b.newPage();
await p.setViewport({ width: 5240, height: 3930, deviceScaleFactor: Number(scale || 1) });
await p.goto('file://' + svg, { waitUntil: 'networkidle0' });
await p.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 500));
await p.screenshot({ path: png, clip: { x: 0, y: 0, width: 5240, height: 3930 } });
await b.close();
