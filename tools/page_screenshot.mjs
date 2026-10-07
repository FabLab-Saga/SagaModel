// Screenshot a JS page + dump its text/images: node page_screenshot.mjs <url> <out.png>
import puppeteer from 'puppeteer-core';
const [url, out] = process.argv.slice(2);
const b = await puppeteer.launch({ executablePath: '/usr/bin/google-chrome', headless: 'new' });
const p = await b.newPage(); await p.setViewport({ width: 1400, height: 900 });
await p.goto(url, { waitUntil: 'networkidle2', timeout: 90000 });
for (let y = 0; y < 20; y++) { await p.evaluate(() => window.scrollBy(0, 900)); await new Promise(r => setTimeout(r, 700)); }
await p.evaluate(() => window.scrollTo(0, 0)); await new Promise(r => setTimeout(r, 1500));
await p.screenshot({ path: out, fullPage: true });
console.log(await p.evaluate(() => document.body.innerText.slice(0, 3000)));
const imgs = await p.evaluate(() => [...document.images].map(i => i.currentSrc).filter(Boolean));
console.log('IMAGES', imgs.length); console.log(imgs.slice(0, 60).join('\n'));
await b.close();
