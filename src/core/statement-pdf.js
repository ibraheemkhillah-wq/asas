/**
 * كشف الحساب كملف PDF جاهز للإرسال للعميل على واتساب.
 *
 * الطريقة: نبني صفحة HTML بهوية الشركة (عربية RTL) ثم نطبعها PDF عبر
 * متصفّح Chrome/Chromium المثبَّت على الخادم (خيار --print-to-pdf المدمج فيه).
 * لا مكتبات PDF خارجية: المتصفّح وحده يعالج تشكيل الحروف العربية واتجاه النص
 * معالجة صحيحة، وهو ما تفشل فيه معظم مكتبات PDF الجاهزة.
 *
 * إن لم يوجد متصفّح على الخادم، يبقى مسار الطباعة اليدوية متاحاً:
 * صفحة HTML جاهزة للطباعة يحفظها المستخدم PDF من متصفّحه.
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { HttpError } from '../lib/http.js';
import { log } from '../lib/log.js';
import * as accounting from './accounting.js';
import * as files from './files.js';
import * as fx from './fx.js';

const run = promisify(execFile);

const BRAND = '#1b2a56';
const esc = (value) =>
  String(value ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );

/** شعار الشركة مضمَّناً في الصفحة (لا يعتمد على أي ملف خارجي عند الطباعة) */
function logoMark() {
  try {
    const file = path.resolve(process.cwd(), 'public/logo-mark.svg');
    return `<img class="logo" src="data:image/svg+xml;base64,${fs
      .readFileSync(file)
      .toString('base64')}" alt="">`;
  } catch {
    return '';
  }
}

const money = (amount, currency) =>
  `<span class="num">${fx.fmt(amount, currency)}</span>`;

/** المبالغ غير الصفرية بعملتيها: «2,820 ₺ و 50 $» */
const both = (amounts) => {
  const parts = fx.CURRENCIES.filter((c) => Math.abs(amounts[c]) > 0.005).map((c) =>
    fx.fmt(amounts[c], c),
  );
  return `<span class="num">${parts.length ? parts.join('  و  ') : fx.fmt(0, 'TRY')}</span>`;
};

/** صفحة الكشف بهوية الشركة — تُستخدم للطباعة وللتحويل إلى PDF */
export function statementHtml(stmt, { company = 'CALL & RENT' } = {}) {
  if (!stmt.found) throw new HttpError(404, stmt.message);

  const used = fx.CURRENCIES.filter((c) => stmt.byCurrency[c].entries > 0);
  const sign = stmt.status === 'customer_owes' ? -1 : 1;

  const summary = stmt.mixed
    ? `<div class="final">
         <div class="line ok"><span>مستحق لك</span> <b>${both(stmt.toRefund)}</b></div>
         <div class="line due"><span>مستحق علينا منك</span> <b>${both(stmt.toCollect)}</b></div>
       </div>`
    : stmt.status === 'company_owes'
      ? `<div class="final ok"><span>الرصيد النهائي — مستحق لك</span> <b>${both(stmt.toRefund)}</b></div>`
      : stmt.status === 'customer_owes'
        ? `<div class="final due"><span>الرصيد النهائي — مستحق علينا منك</span> <b>${both(stmt.toCollect)}</b></div>`
        : '<div class="final settled"><span>الرصيد النهائي</span> <b>صفر — الحساب مصفّى بالكامل</b></div>';

  const rateLine =
    stmt.combined && stmt.fx?.rate
      ? `<p class="rate">
           ${stmt.mixed ? 'صافي الفرق بعد التحويل' : 'المكافئ الإجمالي'}:
           <span class="num">${fx.fmt(sign * stmt.combined.inTRY, 'TRY')}</span>
           أو <span class="num">${fx.fmt(sign * stmt.combined.inUSD, 'USD')}</span>
           <br>سعر الصرف المعتمد:
           <span class="num">1 $ = ${fx.fmt(stmt.fx.rate, 'TRY')}</span>
           — المصدر: ${esc(stmt.fx.source)}
         </p>`
      : '';

  return `<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>كشف حساب — ${esc(stmt.customer.name)}</title>
<style>
  @page { size: A4; margin: 14mm 12mm; }
  * { box-sizing: border-box; }
  body {
    font-family: "Noto Sans Arabic", "Segoe UI", Tahoma, "Geeza Pro", sans-serif;
    color: #131a2b; margin: 0; font-size: 12.5px; line-height: 1.65;
  }
  .num { direction: ltr; unicode-bidi: isolate; font-variant-numeric: tabular-nums; white-space: nowrap; }

  header { display: flex; justify-content: space-between; align-items: flex-start;
           border-bottom: 3px solid ${BRAND}; padding-bottom: 10px; margin-bottom: 14px; }
  .brand { display: flex; align-items: center; gap: 10px; }
  .logo { width: 40px; height: 40px; }
  .brand b { font-size: 19px; font-weight: 800; letter-spacing: 2px; color: ${BRAND}; display: block; }
  .brand span { font-size: 11px; color: #5a6478; }
  .doc { text-align: left; }
  .doc b { font-size: 15px; color: ${BRAND}; display: block; }
  .doc span { font-size: 11px; color: #5a6478; }

  .who { background: #f3f5fa; border-radius: 8px; padding: 9px 12px; margin-bottom: 14px;
         display: flex; gap: 22px; flex-wrap: wrap; }
  .who div span { color: #5a6478; }

  h2 { font-size: 12px; color: #5a6478; letter-spacing: .4px; margin: 16px 0 7px; }

  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 6px 8px; text-align: right; border-bottom: 1px solid #e3e7f0; }
  thead th { background: ${BRAND}; color: #fff; font-weight: 600; font-size: 11.5px; border: 0; }
  tbody tr:nth-child(even) { background: #f8f9fc; }
  td.note { color: #5a6478; font-size: 11px; }
  .credit { color: #0f7a51; }
  .debit { color: #bb2f26; }

  .totals { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px; }
  .totals .box { flex: 1 1 210px; border: 1px solid #dbe0ea; border-radius: 9px; padding: 9px 11px; }
  .totals .box h3 { margin: 0 0 5px; font-size: 12.5px; color: ${BRAND}; }
  .totals .box div { display: flex; justify-content: space-between; }
  .totals .box div span:first-child { color: #5a6478; }

  .final { border: 2px solid ${BRAND}; border-radius: 10px; padding: 11px 14px; margin-top: 14px;
           font-size: 15px; display: flex; justify-content: space-between; align-items: center; gap: 14px; }
  .final b { font-size: 18px; }
  .final .line { display: flex; justify-content: space-between; width: 100%; }
  .final.ok, .final .line.ok b { color: #0f7a51; }
  .final.due, .final .line.due b { color: #bb2f26; }
  .final.settled { color: ${BRAND}; }
  .final:has(.line) { flex-direction: column; align-items: stretch; gap: 6px; }

  .rate { font-size: 11.5px; color: #5a6478; margin: 8px 2px 0; }
  footer { margin-top: 18px; border-top: 1px solid #e3e7f0; padding-top: 9px;
           font-size: 10.5px; color: #5a6478; display: flex; justify-content: space-between; }
</style></head>
<body>
  <header>
    <div class="brand">
      ${logoMark()}
      <div>
        <b>${esc(company)}</b>
        <span>تأجير السيارات — إسطنبول · Drive Your Dreams, Discover Istanbul</span>
      </div>
    </div>
    <div class="doc">
      <b>كشف حساب</b>
      <span class="num">${esc(String(stmt.generatedAt).slice(0, 10))}</span>
    </div>
  </header>

  <div class="who">
    <div><span>العميل:</span> <b>${esc(stmt.customer.name)}</b></div>
    ${stmt.customer.phone ? `<div><span>الهاتف:</span> <b class="num">${esc(stmt.customer.phone)}</b></div>` : ''}
    ${stmt.customer.idNumber ? `<div><span>الهوية:</span> <b class="num">${esc(stmt.customer.idNumber)}</b></div>` : ''}
  </div>

  <h2>تفاصيل الحركات</h2>
  <table>
    <thead><tr>
      <th>التاريخ</th><th>البيان</th><th>المرجع</th><th>لك</th><th>عليك</th><th>الرصيد</th>
    </tr></thead>
    <tbody>
      ${stmt.entries
        .map(
          (e) => `<tr>
            <td class="num">${esc(e.date)}</td>
            <td>${esc(e.label)}${e.note ? `<div class="note">${esc(e.note)}</div>` : ''}</td>
            <td>${esc(e.ref || '—')}</td>
            <td class="credit">${e.credit ? money(e.credit, e.currency) : '—'}</td>
            <td class="debit">${e.debit ? money(e.debit, e.currency) : '—'}</td>
            <td><b>${money(e.running, e.currency)}</b></td>
          </tr>`,
        )
        .join('')}
    </tbody>
  </table>

  <h2>الملخّص</h2>
  <div class="totals">
    ${used
      .map(
        (c) => `<div class="box">
          <h3>${c === 'TRY' ? 'الليرة التركية' : 'الدولار'}</h3>
          <div><span>ما دفعته وتأميناتك</span> ${money(stmt.byCurrency[c].credits, c)}</div>
          <div><span>المستحقات عليك</span> ${money(stmt.byCurrency[c].debits, c)}</div>
          <div><span>تأمينات محفوظة</span> ${money(stmt.byCurrency[c].depositsHeld, c)}</div>
          <div><span><b>الرصيد</b></span> <b>${money(stmt.byCurrency[c].net, c)}</b></div>
        </div>`,
      )
      .join('')}
  </div>

  ${summary}
  ${rateLine}

  <footer>
    <span>${esc(company)} — كشف صادر آلياً من نظام إدارة العمليات</span>
    <span class="num">${esc(String(stmt.generatedAt).slice(0, 16).replace('T', ' '))}</span>
  </footer>
</body></html>`;
}

// ===== إيجاد متصفّح للطباعة =====

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

/** تحويل صفحة HTML إلى PDF عبر المتصفّح */
export async function htmlToPdf(html) {
  const chrome = findChrome();
  if (!chrome) {
    throw new HttpError(
      501,
      'لا يوجد متصفّح Chrome/Chromium على الخادم لتوليد PDF. ' +
        'ثبّت chromium (مثال: apt install chromium) أو اضبط PDF_CHROME_PATH، ' +
        'أو استخدم صفحة الطباعة /api/accounting/statement.html واحفظها PDF من المتصفّح.',
    );
  }

  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'callrent-pdf-'));
  const htmlFile = path.join(dir, 'statement.html');
  const pdfFile = path.join(dir, 'statement.pdf');
  fs.writeFileSync(htmlFile, html, 'utf8');

  try {
    await run(
      chrome,
      [
        '--headless=new',
        '--disable-gpu',
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--no-pdf-header-footer',
        `--user-data-dir=${path.join(dir, 'profile')}`,
        `--print-to-pdf=${pdfFile}`,
        `file://${htmlFile}`,
      ],
      { timeout: 45000 },
    );
    if (!fs.existsSync(pdfFile)) throw new Error('لم يُنتج المتصفّح ملف PDF');
    return fs.readFileSync(pdfFile);
  } catch (err) {
    throw new HttpError(500, `تعذّر توليد PDF: ${err.message}`);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

/** اسم ملف مفهوم للعميل: كشف-حساب-أحمد-نصار-2026-08-22.pdf */
function fileNameFor(stmt) {
  const name = String(stmt.customer.name || 'عميل').trim().replace(/\s+/g, '-');
  return `كشف-حساب-${name}-${String(stmt.generatedAt).slice(0, 10)}.pdf`;
}

/**
 * كشف حساب العميل كملف PDF محفوظ في مكتبة الملفات (فيبقى متاحاً للإرسال لاحقاً).
 * @returns {Promise<{file: object, buffer: Buffer, statement: object}>}
 */
export async function statementPdf(query) {
  const stmt = await accounting.statement(query);
  if (!stmt.found) throw new HttpError(404, stmt.message);

  const buffer = await htmlToPdf(statementHtml(stmt));
  const file = files.saveBuffer({
    name: fileNameFor(stmt),
    mime: 'application/pdf',
    buffer,
    source: 'generated',
    ref: stmt.customer.id,
    kind: 'statement',
  });
  return { file, buffer, statement: stmt };
}
