/**
 * إيجاد متصفّح Chrome/Chromium على الجهاز.
 *
 * يستخدمه توليد كشوف PDF (‎--print-to-pdf‎) وسائق eganis عبر المتصفّح،
 * فوُضع في وحدة مستقلّة حتى لا يستورد أحدهما الآخر.
 */
import fs from 'node:fs';
import path from 'node:path';
import { log } from './log.js';

const CHROME_CANDIDATES = [
  process.env.PDF_CHROME_PATH,
  process.env.CHROME_PATH,
  '/usr/bin/google-chrome',
  '/usr/bin/google-chrome-stable',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser',
  '/snap/bin/chromium',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
];

/** متصفّحات Playwright المثبَّتة (إن وُجدت) */
function playwrightChromes() {
  const base = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (!base || !fs.existsSync(base)) return [];
  const found = [];
  for (const dir of fs.readdirSync(base)) {
    if (!dir.startsWith('chromium')) continue;
    for (const rel of ['chrome-linux/chrome', 'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-win/chrome.exe']) {
      const full = path.join(base, dir, rel);
      if (fs.existsSync(full)) found.push(full);
    }
  }
  return found;
}

let cachedChrome;

export function findChrome() {
  if (cachedChrome !== undefined) return cachedChrome;
  const all = [...CHROME_CANDIDATES.filter(Boolean), ...playwrightChromes()];
  cachedChrome = all.find((p) => {
    try {
      return fs.existsSync(p);
    } catch {
      return false;
    }
  }) || null;
  if (cachedChrome) log.info(`طباعة PDF عبر: ${cachedChrome}`);
  return cachedChrome;
}

