// Capture a SketchUp share link: node sketchup_capture.mjs '<share-url>' <outdir>
// Saves every API response; the .skp arrives as connect-gateway parts (see CLAUDE.md / README).
import puppeteer from 'puppeteer-core';
import fs from 'fs';

const URL = process.argv[2];
const OUT = process.argv[3];
fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: '/usr/bin/google-chrome',
  headless: 'new',
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--window-size=1600,1000'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 1000 });
const log = [];
let n = 0;
page.on('response', async (r) => {
  const u = r.url();
  const ct = r.headers()['content-type'] || '';
  log.push(`${r.status()} ${r.request().method()} ${ct} ${u}`);
  if (/app_static|google|fonts|gtag|analytics|\.js$|\.css$|\.png$|\.svg$|\.woff/.test(u)) return;
  try {
    const b = await r.buffer();
    if (b.length > 0) fs.writeFileSync(`${OUT}/resp_${String(n++).padStart(3, '0')}.bin`, b), log.push(`   -> resp_${String(n - 1).padStart(3, '0')}.bin ${b.length}B`);
  } catch {}
});
page.on('console', (m) => log.push(`CONSOLE ${m.type()}: ${m.text()}`));
await page.goto(URL, { waitUntil: 'networkidle2', timeout: 90000 }).catch((e) => log.push('GOTO ' + e));
await new Promise((r) => setTimeout(r, 20000));
await page.screenshot({ path: `${OUT}/shot.png` });
fs.writeFileSync(`${OUT}/log.txt`, log.join('\n'));
fs.writeFileSync(`${OUT}/dom.txt`, await page.evaluate(() => document.body.innerText));
await browser.close();
