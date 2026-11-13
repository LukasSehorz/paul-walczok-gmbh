// Zeichnet ein SVG mit Chrome in eine PNG-Datei (weisser Grund).
// Aufruf: node render.js <in.svg> <out.png> <breite>
// Braucht puppeteer-core; Pfad per Umgebungsvariable PUPPETEER_CORE, sonst
// require('puppeteer-core'). Chrome unter CHROME_PATH oder /Applications.
const fs = require('fs');
const puppeteer = require(process.env.PUPPETEER_CORE || 'puppeteer-core');
(async () => {
  const [, , svgPath, out, w] = process.argv;
  const svg = fs.readFileSync(svgPath, 'utf8');
  const vb = svg.match(/viewBox="([^"]+)"/)[1].split(/\s+/).map(Number);
  const W = +w, H = Math.round(W * vb[3] / vb[2]);
  const b = await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
  });
  const p = await b.newPage();
  await p.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
  await p.setContent('<html><body style="margin:0;background:#fff">' +
    svg.replace('<svg ', `<svg width="${W}" height="${H}" style="display:block" `) + '</body></html>');
  await p.screenshot({ path: out });
  await b.close();
})();
