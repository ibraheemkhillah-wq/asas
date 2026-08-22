/**
 * مستكشف لوحة eganis — يجهّز الربط عبر المتصفّح دون الحاجة إلى API.
 *
 * لا يُرسل شيئاً لأي جهة: كل المخرجات تُحفظ عندك في data/eganis-inspect/،
 * وكلمة السر تبقى في .env على جهازك ولا تظهر في أي ملف مخرَج.
 *
 * الاستخدام (على جهاز فيه شاشة — كمبيوتر المكتب، لا الخادم):
 *
 *   1) npm i playwright && npx playwright install chromium
 *
 *   2) npm run eganis:inspect -- login
 *      يفتح متصفّحاً مرئياً على لوحة eganis. سجّل الدخول بيدك (حتى لو فيه رمز تحقق)،
 *      ثم ارجع للطرفية واضغط Enter. تُحفظ الجلسة في data/eganis-session.json
 *      فلا نحتاج أتمتة كلمة السر إطلاقاً.
 *
 *   3) npm run eganis:inspect -- menu
 *      يسرد كل روابط القوائم في اللوحة — منها نعرف صفحات العقود والمركبات والعملاء.
 *
 *   4) npm run eganis:inspect -- scan /contracts /vehicles
 *      يفتح كل صفحة ويصف جداولها: أسماء الأعمدة، عدد الصفوف، عيّنة من أول صف،
 *      مع لقطة شاشة ونسخة HTML لكل صفحة.
 *
 * أرسل لي ملف data/eganis-inspect/summary.json وأكتب لك ملف الربط جاهزاً.
 */
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { config } from '../src/config.js';

const OUT_DIR = path.resolve(process.cwd(), 'data/eganis-inspect');
const SESSION_FILE = path.resolve(process.cwd(), 'data/eganis-session.json');

const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const DIM = '\x1b[2m';
const OFF = '\x1b[0m';
const ok = (t) => console.log(`${GREEN}✔${OFF} ${t}`);
const bad = (t) => console.log(`${RED}✘${OFF} ${t}`);
const warn = (t) => console.log(`${YELLOW}!${OFF} ${t}`);
const dim = (t) => console.log(`${DIM}  ${t}${OFF}`);

async function playwright() {
  try {
    return await import('playwright');
  } catch {
    bad('حزمة playwright غير مثبّتة.');
    dim('نفّذ: npm i playwright && npx playwright install chromium');
    process.exit(1);
  }
}

function requireBaseUrl() {
  if (!config.eganis.baseUrl) {
    bad('EGANIS_BASE_URL غير محدّد في ملف .env');
    dim('مثال: EGANIS_BASE_URL=https://panel.eganis.com.tr');
    process.exit(1);
  }
  return config.eganis.baseUrl;
}

const waitForEnter = (message) =>
  new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(`\n${message}\n> `, () => {
      rl.close();
      resolve();
    });
  });

/** تسجيل دخول يدوي مرة واحدة، ثم حفظ الجلسة لإعادة استخدامها */
async function login() {
  const { chromium } = await playwright();
  const baseUrl = requireBaseUrl();

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext({ locale: 'tr-TR', viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  console.log(`\nفتح ${baseUrl} …`);
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded' }).catch(() => {});

  await waitForEnter('سجّل الدخول في نافذة المتصفّح، وبعد ما تفتح اللوحة اضغط Enter هنا.');

  fs.mkdirSync(path.dirname(SESSION_FILE), { recursive: true });
  await context.storageState({ path: SESSION_FILE });
  ok(`تم حفظ الجلسة: ${SESSION_FILE}`);
  dim('هذا الملف يحوي كوكيز جلستك — لا ترسله لأحد، وضعه فقط على خادمك.');

  // أول تشخيص: أين انتهى بنا المطاف بعد الدخول؟
  ok(`الصفحة الحالية: ${page.url()}`);
  await browser.close();
}

async function withSession(fn) {
  const { chromium } = await playwright();
  const baseUrl = requireBaseUrl();
  if (!fs.existsSync(SESSION_FILE)) {
    bad('لا توجد جلسة محفوظة — نفّذ أولاً: npm run eganis:inspect -- login');
    process.exit(1);
  }
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState: SESSION_FILE, locale: 'tr-TR' });
  try {
    return await fn({ context, baseUrl });
  } finally {
    await browser.close();
  }
}

/** سرد روابط القوائم لمعرفة صفحات اللوحة */
async function menu() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  await withSession(async ({ context, baseUrl }) => {
    const page = await context.newPage();
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);

    const links = await page.$$eval('a[href]', (nodes) =>
      nodes
        .map((a) => ({ text: a.textContent.trim().replace(/\s+/g, ' ').slice(0, 60), href: a.getAttribute('href') }))
        .filter((l) => l.text && l.href && !l.href.startsWith('javascript') && !l.href.startsWith('#')),
    );

    // إزالة التكرار مع الحفاظ على الترتيب
    const seen = new Set();
    const unique = links.filter((l) => !seen.has(l.href) && seen.add(l.href));

    ok(`${unique.length} رابطاً في اللوحة`);
    for (const l of unique) console.log(`   ${l.text.padEnd(34)} ${DIM}${l.href}${OFF}`);

    fs.writeFileSync(path.join(OUT_DIR, 'menu.json'), JSON.stringify(unique, null, 2), 'utf8');
    await page.screenshot({ path: path.join(OUT_DIR, 'home.png'), fullPage: true });
    ok(`حُفظ: ${path.join(OUT_DIR, 'menu.json')} و home.png`);
    dim('ابعتلي menu.json وأقول لك أي الصفحات نحتاج.');
  });
}

/** وصف جداول صفحة: الأعمدة، عدد الصفوف، عيّنة صف */
async function describePage(page) {
  return page.evaluate(() => {
    const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();

    const tables = [...document.querySelectorAll('table')].map((table, index) => {
      const headers = [...table.querySelectorAll('thead th, tr:first-child th')].map((th) => clean(th.textContent));
      const rows = [...table.querySelectorAll('tbody tr')];
      const firstRow = rows[0] ? [...rows[0].children].map((td) => clean(td.textContent).slice(0, 40)) : [];
      return {
        index,
        id: table.id || null,
        className: table.className || null,
        headers,
        rowCount: rows.length,
        firstRow,
      };
    });

    // شبكات بيانات لا تستخدم <table> (كثير من اللوحات الحديثة)
    const grids = [...document.querySelectorAll('[role="grid"], [role="table"], .k-grid, .dataTables_wrapper, .ag-root')]
      .slice(0, 5)
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        id: el.id || null,
        className: (el.className || '').toString().slice(0, 120),
        role: el.getAttribute('role'),
      }));

    const inputs = [...document.querySelectorAll('input:not([type=hidden]), select')]
      .slice(0, 25)
      .map((el) => ({
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type'),
        name: el.getAttribute('name'),
        id: el.id || null,
        placeholder: el.getAttribute('placeholder'),
      }));

    return { title: document.title, url: location.href, tables, grids, inputs };
  });
}

/** فحص صفحات محدّدة وحفظ وصفها ولقطاتها */
async function scan(paths) {
  if (!paths.length) {
    bad('حدّد صفحة واحدة على الأقل، مثال: npm run eganis:inspect -- scan /contracts');
    process.exit(1);
  }
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const summary = await withSession(async ({ context, baseUrl }) => {
    const results = [];
    for (const target of paths) {
      const url = target.startsWith('http') ? target : `${baseUrl}${target.startsWith('/') ? '' : '/'}${target}`;
      const page = await context.newPage();
      const safe = target.replace(/[^\w؀-ۿ-]+/g, '_').replace(/^_|_$/g, '') || 'page';

      try {
        console.log(`\nفحص ${url} …`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(3500); // انتظار الجداول التي تُحمّل بجافاسكربت

        const described = await describePage(page);
        described.path = target;
        results.push(described);

        fs.writeFileSync(path.join(OUT_DIR, `${safe}.html`), await page.content(), 'utf8');
        await page.screenshot({ path: path.join(OUT_DIR, `${safe}.png`), fullPage: true });

        ok(`${described.title || target}`);
        if (!described.tables.length && !described.grids.length) {
          warn('   لا يوجد جدول ظاهر — قد تكون البيانات داخل إطار iframe أو تحتاج ضغطة بحث أولاً.');
        }
        for (const t of described.tables) {
          if (!t.rowCount) continue;
          console.log(`   جدول #${t.index}${t.id ? ` (id=${t.id})` : ''}: ${t.rowCount} صف`);
          dim(`     الأعمدة: ${t.headers.join(' | ') || '(بلا ترويسة)'}`);
          dim(`     أول صف: ${t.firstRow.join(' | ')}`);
        }
      } catch (err) {
        bad(`${target} — ${err.message}`);
        results.push({ path: target, error: err.message });
      } finally {
        await page.close();
      }
    }
    return results;
  });

  const file = path.join(OUT_DIR, 'summary.json');
  fs.writeFileSync(file, JSON.stringify(summary, null, 2), 'utf8');
  console.log('');
  ok(`حُفظ الوصف الكامل: ${file}`);
  dim('راجع الصور و HTML قبل الإرسال — واحذف أي بيانات عملاء حسّاسة لا تريد مشاركتها.');
}

const [command, ...rest] = process.argv.slice(2);

const commands = {
  login,
  menu,
  scan: () => scan(rest),
};

if (!commands[command]) {
  console.log(`
الاستخدام:
  npm run eganis:inspect -- login              تسجيل دخول يدوي مرة واحدة وحفظ الجلسة
  npm run eganis:inspect -- menu               سرد صفحات اللوحة
  npm run eganis:inspect -- scan /contracts    وصف جداول صفحة أو أكثر
`);
  process.exit(1);
}

commands[command]().catch((err) => {
  bad(err.message);
  process.exit(1);
});
