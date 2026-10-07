// Extract the Fab Lab icon (paths 3-5) from the official logo SVG: node extract_logo_icon.mjs <logo.svg> <icon.svg>
import puppeteer from 'puppeteer-core';
import fs from 'fs';
const [src, dst] = process.argv.slice(2);
const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new' });
const p = await b.newPage();
await p.setContent(`<html><body>${fs.readFileSync(src, 'utf8')}</body></html>`);
const out = await p.evaluate(() => {
  const svg = document.querySelector('svg');
  [...svg.querySelectorAll('path')].forEach((el, i) => { if (![3, 4, 5].includes(i)) el.remove(); });
  // tight viewBox around the remaining icon, in root user units
  const pts = [...svg.querySelectorAll('path')].map(el => { const bb = el.getBBox(); const m = el.getCTM(), r = svg.getCTM().inverse().multiply(m);
    return [[bb.x, bb.y], [bb.x + bb.width, bb.y + bb.height]].map(([x, y]) => new DOMPoint(x, y).matrixTransform(r)); }).flat();
  const x0 = Math.min(...pts.map(q => q.x)), y0 = Math.min(...pts.map(q => q.y)), x1 = Math.max(...pts.map(q => q.x)), y1 = Math.max(...pts.map(q => q.y));
  svg.setAttribute('viewBox', `${x0} ${y0} ${x1 - x0} ${y1 - y0}`); svg.removeAttribute('width'); svg.removeAttribute('height');
  return svg.outerHTML;
});
fs.writeFileSync(dst, out); await b.close();
