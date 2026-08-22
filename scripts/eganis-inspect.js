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
import { findChrome } from '../src/core/statement-pdf.js';

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
    dim('نفّذ: npm i playwright');
    process.exit(1);
  }
}

/**
 * تشغيل المتصفّح: نستخدم Chrome/Chromium المثبَّت على الجهاز إن وُجد،
 * فلا يحتاج المستخدم تنزيل متصفّح إضافي (npx playwright install).
 */
async function launch(options = {}) {
  const { chromium } = await playwright();
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_PATH || findChrome() || undefined;
  try {
    return await chromium.launch({ ...options, executablePath });
  } catch (err) {
    if (executablePath) {
      // المتصفّح الموجود رفض التشغيل — نجرّب متصفّح Playwright نفسه
      try {
        return await chromium.launch(options);
      } catch {
        /* نُظهر الخطأ الأصلي أدناه */
      }
    }
    bad(`تعذّر تشغيل المتصفّح: ${err.message.split('\n')[0]}`);
    dim('ثبّت Google Chrome، أو نفّذ: npx playwright install chromium');
    dim('أو حدّد المسار يدوياً: PLAYWRIGHT_CHROMIUM_PATH=/path/to/chrome');
    process.exit(1);
  }
}

const ask = (question) =>
  new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    rl.question(`\n${question}\n> `, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });

const waitForEnter = (message) => ask(message);

const BASE_URL_FILE = path.resolve(process.cwd(), 'data/eganis-base-url.txt');

/** عنوان اللوحة: من .env أو من ملف محفوظ أو نسأل عنه مباشرة */
async function resolveBaseUrl() {
  if (config.eganis.baseUrl) return config.eganis.baseUrl;
  if (fs.existsSync(BASE_URL_FILE)) return fs.readFileSync(BASE_URL_FILE, 'utf8').trim();

  const answer = await ask(
    'ما رابط لوحة eganis التي تفتحها كل يوم؟ (انسخه من شريط عنوان المتصفّح)\nمثال: https://panel.eganis.com.tr',
  );
  const url = answer.replace(/\/+$/, '');
  if (!/^https?:\/\//i.test(url)) {
    bad('الرابط يجب أن يبدأ بـ https:// أو http://');
    process.exit(1);
  }
  fs.mkdirSync(path.dirname(BASE_URL_FILE), { recursive: true });
  fs.writeFileSync(BASE_URL_FILE, url, 'utf8');
  ok(`حُفظ الرابط — لن نسأل عنه مرة أخرى (${BASE_URL_FILE})`);
  return url;
}

/** تسجيل دخول يدوي مرة واحدة، ثم حفظ الجلسة لإعادة استخدامها */
async function login() {
  const baseUrl = await resolveBaseUrl();

  const browser = await launch({ headless: false });
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
  const baseUrl = await resolveBaseUrl();
  if (!fs.existsSync(SESSION_FILE)) {
    bad('لا توجد جلسة محفوظة — نفّذ أولاً: npm run eganis:inspect -- login');
    process.exit(1);
  }
  const browser = await launch({ headless: true });
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

/**
 * إخفاء البيانات الشخصية من العيّنات: نحتفظ بشكل القيمة (كم رقماً، كيف تُنسَّق)
 * لأنه ما نحتاجه لمطابقة الأعمدة، ونستبدل المحتوى الحسّاس.
 */
function redact(value) {
  return String(value)
    .replace(/[\w.+-]+@[\w.-]+\.\w+/g, '«بريد»')
    .replace(/\d[\d\s()+-]{7,}\d/g, (m) => `«رقم ${m.replace(/\D/g, '').length} خانة»`)
    .replace(/\b\d{9,}\b/g, (m) => `«رقم ${m.length} خانة»`);
}

function redactDescribed(described, enabled) {
  if (!enabled) return described;
  for (const table of described.tables || []) {
    table.firstRow = (table.firstRow || []).map(redact);
  }
  return described;
}

/** الصفحات التي تهمّنا، بكلمات تركية وإنجليزية كما تسمّيها لوحات eganis */
// الترتيب مقصود: الأكثر تحديداً أولاً. تجنّبنا كلمات قصيرة تتداخل
// (مثل "car" التي تقع داخل "cari hesap" وتعني الحساب لا المركبة).
const PAGE_HINTS = [
  { kind: 'ledger', words: ['cari', 'hesap', 'tahsilat', 'odeme', 'ödeme', 'kasa', 'ekstre', 'account', 'payment'] },
  { kind: 'contracts', words: ['sozlesme', 'sözleşme', 'kiralama', 'contract', 'rental'] },
  { kind: 'bookings', words: ['rezervasyon', 'reservation', 'booking'] },
  { kind: 'customers', words: ['musteri', 'müşteri', 'customer', 'client'] },
  { kind: 'vehicles', words: ['arac', 'araç', 'vehicle', 'filo', 'fleet', 'plaka'] },
  { kind: 'documents', words: ['belge', 'dosya', 'evrak', 'document', 'foto', 'resim'] },
];

function classify(link) {
  const haystack = `${link.text} ${link.href}`.toLowerCase();
  for (const hint of PAGE_HINTS) {
    if (hint.words.some((w) => haystack.includes(w))) return hint.kind;
  }
  return null;
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
async function scan(paths, { mask = true, labels = {} } = {}) {
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

        const described = redactDescribed(await describePage(page), mask);
        described.path = target;
        described.kind = labels[target] || null;
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
  if (mask) {
    dim('أرقام الهواتف والهويات في العيّنات مُخفاة — الشكل محفوظ وهو ما نحتاجه للمطابقة.');
    dim('(للاحتفاظ بالقيم كما هي: أضِف --raw)');
  }
  dim(`لقطات الشاشة و HTML في ${OUT_DIR} — راجعها قبل مشاركة أي منها.`);
  return summary;
}

/**
 * أمر واحد يكفي: يفتح اللوحة، يلتقط روابط القوائم، يخمّن صفحات
 * العقود والمركبات والحجوزات والعملاء والحسابات، ثم يصفها كلها.
 */
async function auto(args) {
  const mask = !args.includes('--raw');
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const picked = await withSession(async ({ context, baseUrl }) => {
    const page = await context.newPage();
    console.log(`\nفتح اللوحة ${baseUrl} …`);
    await page.goto(baseUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(3000);

    const links = await page.$$eval('a[href]', (nodes) =>
      nodes
        .map((a) => ({
          text: a.textContent.trim().replace(/\s+/g, ' ').slice(0, 60),
          href: a.getAttribute('href'),
        }))
        .filter((l) => l.href && !l.href.startsWith('javascript') && !l.href.startsWith('#')),
    );
    const seen = new Set();
    const unique = links.filter((l) => !seen.has(l.href) && seen.add(l.href));
    fs.writeFileSync(path.join(OUT_DIR, 'menu.json'), JSON.stringify(unique, null, 2), 'utf8');
    await page.screenshot({ path: path.join(OUT_DIR, 'home.png'), fullPage: true });
    ok(`${unique.length} رابطاً في اللوحة (menu.json)`);

    // أول رابط مطابق لكل نوع يكفي
    const chosen = {};
    for (const link of unique) {
      const kind = classify(link);
      if (kind && !chosen[kind]) chosen[kind] = link;
    }
    await page.close();
    return chosen;
  });

  const kinds = Object.keys(picked);
  if (!kinds.length) {
    warn('لم أتعرّف على صفحات من أسماء الروابط.');
    dim('نفّذ: npm run eganis:inspect -- menu ثم أرسل لي menu.json وأحدّد الصفحات بنفسي.');
    return;
  }

  console.log('\nالصفحات التي سأفحصها:');
  for (const kind of kinds) console.log(`   ${kind.padEnd(11)} ${picked[kind].text} ${DIM}${picked[kind].href}${OFF}`);

  const labels = {};
  for (const kind of kinds) labels[picked[kind].href] = kind;

  await scan(kinds.map((k) => picked[k].href), { mask, labels });

  console.log('');
  ok('جاهز — أرسل لي هذين الملفين:');
  console.log(`   ${path.join(OUT_DIR, 'summary.json')}`);
  console.log(`   ${path.join(OUT_DIR, 'menu.json')}`);
}

const [command, ...rest] = process.argv.slice(2);

const commands = {
  login,
  menu,
  auto: () => auto(rest),
  scan: () => scan(rest.filter((a) => !a.startsWith('--')), { mask: !rest.includes('--raw') }),
};

if (!commands[command]) {
  console.log(`
الاستخدام:
  npm run eganis:inspect -- login              (١) تسجيل دخول يدوي مرة واحدة وحفظ الجلسة
  npm run eganis:inspect -- auto               (٢) اكتشاف الصفحات ووصفها تلقائياً — يكفي عادةً

  npm run eganis:inspect -- menu               سرد كل روابط اللوحة (عند فشل الاكتشاف)
  npm run eganis:inspect -- scan /contracts    وصف صفحة أو أكثر بنفسك
  أضِف --raw لعدم إخفاء أرقام الهواتف والهويات في العيّنات
`);
  process.exit(1);
}

commands[command]().catch((err) => {
  bad(err.message);
  process.exit(1);
});
