// Screenshot delle viste della dashboard e rilevamento card in errore.
// Uso: HI_URL=http://localhost:8123 HI_TOKEN=<token> node tests/e2e/screenshots.mjs [cartella_output]
// Richiede Playwright (npm i playwright) e Chromium.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright'); // NODE_PATH=$(npm root -g) se installato globalmente
import fs from 'node:fs';

const url = process.env.HI_URL || 'http://localhost:8123';
const token = process.env.HI_TOKEN;
const out = process.argv[2] || 'tests/report/screenshots';
const views = ['home', 'casa', 'casa-piano_inferiore', 'casa-mansarda', 'clima', 'energia', 'persone', 'automazioni', 'diagnostica'];
fs.mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2, colorScheme: 'light' });
await ctx.addInitScript(([u, t]) => {
  localStorage.setItem('hassTokens', JSON.stringify({
    hassUrl: u, clientId: u + '/', access_token: t, token_type: 'Bearer',
    expires_in: 315360000, expires: Date.now() + 315360000000, refresh_token: '' }));
  localStorage.setItem('selectedTheme', JSON.stringify({ theme: 'Home Intelligence' }));
}, [url, token]);
const page = await ctx.newPage();
let errori = 0;
for (const v of views) {
  await page.goto(`${url}/home-intelligence/${v}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(3500);
  const n = await page.evaluate(() => {
    const found = [];
    const walk = (root) => root.querySelectorAll('*').forEach((el) => {
      if (el.tagName === 'HUI-ERROR-CARD' || el.tagName === 'HUI-WARNING') found.push(el.tagName);
      if (el.shadowRoot) walk(el.shadowRoot);
    });
    walk(document);
    return found.length;
  });
  errori += n;
  console.log(`${v}: card in errore = ${n}`);
  await page.screenshot({ path: `${out}/${v}.png`, fullPage: true });
}
await browser.close();
process.exit(errori > 0 ? 1 : 0);
