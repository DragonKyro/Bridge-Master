// The app's icons: a playing card (the ace of spades) standing on a gold
// arched bridge over water, on green felt. Writes public/favicon.svg and
// rasterises the same art with headless Chrome into the PWA / home-screen
// PNGs (no dependencies; set CHROME to the browser if it isn't found).
//
//   node scripts/make-icons.mjs

import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(root, 'public');

// The spade from src/ui/cards/cardArt.ts (a 100 × 100 box) and the ace's stroked "A".
const SPADE = 'M50 3C62 22 96 39 96 62C96 77 85 85 73 85C64 85 57 80 53 73C54 84 58 92 67 98H33C42 92 46 84 47 73C43 80 36 85 27 85C15 85 4 77 4 62C4 39 38 22 50 3Z';
const GLYPH_A = 'M0.8 14L5 0.2L9.2 14M2.3 9.2H7.7';

/** The art in a 100 × 100 box. `bleed`: a full square (maskable / iOS) with the art scaled into the safe zone. */
function svg({ bleed = false } = {}) {
  const art =
    // water under the arch
    `<path d="M27 87.5q3.8-2.6 7.6 0t7.6 0 7.6 0 7.6 0 7.6 0" fill="none" stroke="#7fd0ef" stroke-width="2.6" stroke-linecap="round" opacity=".85"/>` +
    `<path d="M33 93q3.4-2.2 6.8 0t6.8 0 6.8 0 6.8 0" fill="none" stroke="#5bb4d8" stroke-width="2.2" stroke-linecap="round" opacity=".6"/>` +
    // the card, tilted, standing on the deck
    `<g transform="rotate(-9 50 63)">` +
    `<rect x="30.5" y="9" width="39" height="56" rx="5" fill="#04150f" opacity=".35" transform="translate(2.2 2.6)"/>` +
    `<rect x="30.5" y="9" width="39" height="56" rx="5" fill="url(#card)" stroke="#0b2a1f" stroke-opacity=".3" stroke-width="1"/>` +
    `<rect x="33" y="11.5" width="34" height="51" rx="3.2" fill="none" stroke="#1b2132" stroke-opacity=".14" stroke-width=".8"/>` +
    `<path transform="translate(34.2 13.4) scale(.62)" d="${GLYPH_A}" fill="none" stroke="#1b2132" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>` +
    `<path transform="translate(38.5 26) scale(.23)" d="${SPADE}" fill="#1b2132"/>` +
    `</g>` +
    // the bridge: a parapet, and the span with its arch
    `<rect x="5" y="61" width="90" height="8.5" rx="2.4" fill="url(#gold)" stroke="#6e4d0c" stroke-opacity=".5" stroke-width=".8"/>` +
    `<path d="M11 69.5H89V89H76.5A30 30 0 0 0 23.5 89H11Z" fill="url(#goldBody)" stroke="#6e4d0c" stroke-opacity=".5" stroke-width=".8" stroke-linejoin="round"/>` +
    `<path d="M14 65.2H86" stroke="#fff3c9" stroke-opacity=".55" stroke-width="1"/>` +
    // stones on the span
    `<path d="M18 75V89M82 75V89M23.5 89 26 84M76.5 89 74 84" stroke="#8a6214" stroke-opacity=".35" stroke-width="1"/>`;
  const defs =
    `<defs>` +
    `<radialGradient id="felt" cx=".5" cy=".36" r=".78"><stop offset="0" stop-color="#2a8762"/><stop offset=".6" stop-color="#155a41"/><stop offset="1" stop-color="#0a3022"/></radialGradient>` +
    `<linearGradient id="gold" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff2c4"/><stop offset=".55" stop-color="#e9c46a"/><stop offset="1" stop-color="#c2902c"/></linearGradient>` +
    `<linearGradient id="goldBody" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e3b955"/><stop offset="1" stop-color="#a87a1c"/></linearGradient>` +
    `<linearGradient id="card" x1="0" y1="0" x2=".35" y2="1"><stop offset="0" stop-color="#fffef8"/><stop offset="1" stop-color="#ece3cd"/></linearGradient>` +
    `</defs>`;
  const bg = bleed
    ? `<rect width="100" height="100" fill="url(#felt)"/>`
    : `<rect width="100" height="100" rx="22" fill="url(#felt)"/><rect x="3.5" y="3.5" width="93" height="93" rx="19" fill="none" stroke="#e9c46a" stroke-opacity=".35" stroke-width="1.2"/>`;
  const body = bleed ? `<g transform="translate(12 12) scale(.76)">${art}</g>` : art;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">${defs}${bg}${body}</svg>`;
}

function findChrome() {
  const candidates = [
    process.env.CHROME,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
  ].filter(Boolean);
  const found = candidates.find((p) => existsSync(p));
  if (!found) throw new Error('No Chrome found; set CHROME to a Chrome / Edge / Chromium binary.');
  return found;
}

function rasterise(chrome, markup, size, file, tmp) {
  const html = join(tmp, `${size}.html`);
  writeFileSync(html, `<!doctype html><html><body style="margin:0;background:transparent">${markup.replace('<svg ', `<svg width="${size}" height="${size}" `)}</body></html>`);
  execFileSync(chrome, [
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--force-device-scale-factor=1',
    '--default-background-color=00000000',
    `--window-size=${size},${size}`,
    `--screenshot=${file}`,
    pathToFileURL(html).href,
  ], { stdio: 'ignore' });
}

const chrome = findChrome();
const tmp = mkdtempSync(join(tmpdir(), 'bm-icons-'));
try {
  writeFileSync(join(out, 'favicon.svg'), svg());
  rasterise(chrome, svg(), 192, join(out, 'icon-192.png'), tmp);
  rasterise(chrome, svg(), 512, join(out, 'icon-512.png'), tmp);
  rasterise(chrome, svg({ bleed: true }), 512, join(out, 'icon-maskable-512.png'), tmp);
  rasterise(chrome, svg({ bleed: true }), 180, join(out, 'apple-touch-icon.png'), tmp);
  rasterise(chrome, svg(), 48, join(tmp, 'preview-48.png'), tmp);
  console.log('icons written to', out);
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
