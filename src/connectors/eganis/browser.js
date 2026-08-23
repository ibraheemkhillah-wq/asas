/**
 * سائق eganis عبر المتصفّح — يعمل بحسابك العادي بلا API.
 *
 * وضعان:
 *
 *  • **تلقائي (الافتراضي)** — لا يحتاج أي إعداد يدوي:
 *      يسجّل الدخول (بجلسة محفوظة أو باسم المستخدم وكلمة السر)، يقرأ قائمة
 *      اللوحة، يتعرّف على صفحات العقود والمركبات والحجوزات والعملاء والحسابات
 *      من أسمائها التركية، ثم يفهم أعمدة كل جدول بالمطابقة (auto-map.js).
 *
 *  • **يدوي** — إن عرّفت `browser.pages` في config/eganis.json، تُستخدم
 *      مساراتك ومحدِّداتك كما هي وتتقدّم على الاكتشاف التلقائي.
 *
 * البيانات تبقى في eganis: نقرأ عند الطلب ونحتفظ بنتيجة قصيرة العمر فقط
 * (EGANIS_CACHE_SECONDS) حتى لا نفتح الصفحة نفسها عشرات المرات في الدقيقة.
 *
 * التثبيت:  npm i playwright
 */
import fs from 'node:fs';
import path from 'node:path';
import { config } from '../../config.js';
import { HttpError } from '../../lib/http.js';
import { log } from '../../lib/log.js';
import { findChrome } from '../../lib/chrome.js';
import { classifyLink, mapRows, mappingScore } from './auto-map.js';

let playwrightModule = null;

async function loadPlaywright() {
  if (playwrightModule) return playwrightModule;
  // playwright الكاملة إن كانت مثبّتة، وإلا playwright-core (تأتي مع التطبيق
  // ولا تنزّل متصفّحاً — نستخدم Chromium المثبَّت على النظام)
  for (const pkg of ['playwright', 'playwright-core']) {
    try {
      playwrightModule = await import(pkg);
      return playwrightModule;
    } catch {
      /* نجرّب التالي */
    }
  }
  throw new HttpError(500, 'حزمة playwright غير مثبّتة. نفّذ: npm i playwright-core');
}

function profile() {
  const file = path.resolve(process.cwd(), config.eganis.endpointsFile);
  if (!fs.existsSync(file)) return {};
  try {
    return JSON.parse(fs.readFileSync(file, 'utf8')).browser || {};
  } catch {
    return {};
  }
}

const PAGES_CACHE = path.resolve(process.cwd(), 'data/eganis-pages.json');

export function createBrowserDriver() {
  let browser = null;
  let context = null;
  let discovered = null;
  const cache = new Map(); // kind → { at, rows }

  const cacheMs = Math.max(0, config.eganis.cacheSeconds) * 1000;

  /**
   * خيارات تشغيل موفّرة للذاكرة — الخطط الصغيرة (٥١٢ ميجا) تكفي المتصفّح
   * بالكاد، فنطفئ كل ما لا نحتاجه: الصور والإضافات والخدمات الخلفية.
   */
  const CHROME_ARGS = [
    '--no-sandbox',
    '--disable-dev-shm-usage', // بلا ذاكرة مشتركة كبيرة داخل الحاويات
    '--disable-gpu',
    '--disable-extensions',
    '--disable-background-networking',
    '--disable-background-timer-throttling',
    '--disable-renderer-backgrounding',
    '--disable-features=TranslateUI,BackForwardCache,AcceptCHFrame',
    '--blink-settings=imagesEnabled=false', // نقرأ جداول لا صوراً
    '--mute-audio',
    '--no-first-run',
    '--js-flags=--max-old-space-size=256',
  ];

  async function launchBrowser() {
    const { chromium } = await loadPlaywright();
    const executablePath = process.env.PLAYWRIGHT_CHROMIUM_PATH || findChrome() || undefined;
    try {
      return await chromium.launch({ headless: true, executablePath, args: CHROME_ARGS });
    } catch (err) {
      if (!executablePath) throw err;
      return chromium.launch({ headless: true, args: CHROME_ARGS });
    }
  }

  /**
   * إغلاق المتصفّح بعد فترة خمول: على خادم صغير لا يبقى المتصفّح مفتوحاً
   * طوال اليوم آكلاً الذاكرة. يُعاد فتحه تلقائياً عند أول طلب.
   */
  let idleTimer = null;
  function scheduleIdleClose() {
    clearTimeout(idleTimer);
    const minutes = config.eganis.idleCloseMinutes;
    if (!minutes) return;
    idleTimer = setTimeout(async () => {
      if (!browser) return;
      log.info('eganis(browser): إغلاق المتصفّح لعدم الاستخدام');
      await context?.close().catch(() => {});
      await browser?.close().catch(() => {});
      context = null;
      browser = null;
    }, minutes * 60000);
    idleTimer.unref?.();
  }

  /** هل نحن داخل اللوحة أم رجعنا لصفحة الدخول؟ */
  async function loggedIn(page) {
    const hasPassword = await page.locator('input[type="password"]').count();
    return hasPassword === 0;
  }

  /**
   * تسجيل دخول تلقائي: نكتشف حقول النموذج بدل الاعتماد على محدِّدات مكتوبة،
   * لأن لوحات eganis تختلف قليلاً بين التركيبات.
   */
  async function autoLogin(page, spec) {
    const { username, password } = config.eganis;
    if (!username || !password) {
      throw new HttpError(
        401,
        'انتهت جلسة eganis ولا توجد بيانات دخول. اضبط EGANIS_USERNAME و EGANIS_PASSWORD، ' +
          'أو جدّد الجلسة بـ: npm run eganis:inspect -- login',
      );
    }

    const passwordField = spec.passwordSelector
      ? page.locator(spec.passwordSelector)
      : page.locator('input[type="password"]').first();
    await passwordField.waitFor({ timeout: 15000 });

    // حقل اسم المستخدم: المعرَّف يدوياً، أو أول حقل نصي قبل حقل كلمة السر
    const userField = spec.usernameSelector
      ? page.locator(spec.usernameSelector)
      : page
          .locator('input[type="text"], input[type="email"], input:not([type]), input[name*="user" i], input[name*="kullanici" i]')
          .first();

    await userField.fill(username);
    await passwordField.fill(password);

    const submit = spec.submitSelector
      ? page.locator(spec.submitSelector)
      : page.locator('button[type="submit"], input[type="submit"], button:has-text("Giriş"), button:has-text("Login")').first();

    await Promise.all([
      page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {}),
      submit.click({ timeout: 15000 }),
    ]);
    await page.waitForTimeout(1500);

    if (!(await loggedIn(page))) {
      throw new HttpError(401, 'فشل تسجيل الدخول إلى eganis — تحقّق من اسم المستخدم وكلمة السر');
    }
    log.info('eganis(browser): تم تسجيل الدخول');
  }

  async function session() {
    if (context) return { context, spec: profile() };
    const spec = profile();
    if (!config.eganis.baseUrl) throw new HttpError(500, 'EGANIS_BASE_URL غير محدّد');

    browser = await launchBrowser();
    const sessionFile = path.resolve(
      process.cwd(),
      spec.sessionFile || config.eganis.sessionFile || 'data/eganis-session.json',
    );

    // جلسة محفوظة بتسجيل دخول يدوي — تتجاوز رمز التحقق ولا تحتاج كلمة السر
    if (fs.existsSync(sessionFile)) {
      context = await browser.newContext({ storageState: sessionFile, locale: 'tr-TR' });
      log.info(`eganis(browser): جلسة محفوظة (${path.basename(sessionFile)})`);
    } else {
      context = await browser.newContext({ locale: 'tr-TR' });
    }

    // تحقّق من صلاحية الجلسة، وسجّل الدخول إن لزم
    const page = await context.newPage();
    await page.goto(config.eganis.baseUrl, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1200);
    if (!(await loggedIn(page))) {
      await autoLogin(page, spec);
      // احفظ الجلسة الجديدة لإعادة استخدامها بعد إعادة التشغيل
      try {
        fs.mkdirSync(path.dirname(sessionFile), { recursive: true });
        await context.storageState({ path: sessionFile });
        fs.chmodSync(sessionFile, 0o600);
      } catch (err) {
        log.warn(`تعذّر حفظ جلسة eganis: ${err.message}`);
      }
    }
    await page.close();
    scheduleIdleClose();
    return { context, spec };
  }

  /** اكتشاف صفحات اللوحة مرة واحدة، مع تخزينها لتسريع الإقلاع لاحقاً */
  async function discoverPages() {
    if (discovered) return discovered;

    const spec = profile();
    if (spec.pages && Object.keys(spec.pages).length) {
      discovered = Object.fromEntries(
        Object.entries(spec.pages).map(([kind, page]) => [kind, { href: page.path, manual: page }]),
      );
      return discovered;
    }

    if (fs.existsSync(PAGES_CACHE)) {
      try {
        discovered = JSON.parse(fs.readFileSync(PAGES_CACHE, 'utf8'));
        return discovered;
      } catch {
        /* ملف تالف — نكتشف من جديد */
      }
    }

    const { context: ctx } = await session();
    const page = await ctx.newPage();
    try {
      await page.goto(config.eganis.baseUrl, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(2500);
      const links = await page.$$eval('a[href]', (nodes) =>
        nodes
          .map((a) => ({
            text: (a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
            href: a.getAttribute('href'),
          }))
          .filter((l) => l.href && !l.href.startsWith('javascript') && !l.href.startsWith('#')),
      );

      const found = {};
      for (const link of links) {
        const kind = classifyLink(link);
        if (kind && !found[kind]) found[kind] = { href: link.href, text: link.text };
      }
      discovered = found;

      fs.mkdirSync(path.dirname(PAGES_CACHE), { recursive: true });
      fs.writeFileSync(PAGES_CACHE, JSON.stringify(found, null, 2), 'utf8');
      log.info(`eganis(browser): اكتُشفت الصفحات — ${Object.keys(found).join(', ') || 'لا شيء'}`);
      return discovered;
    } finally {
      await page.close();
    }
  }

  /** كل جداول الصفحة كنصوص (ترويسة + صفوف) */
  async function readTables(page) {
    return page.evaluate(() => {
      const clean = (t) => (t || '').replace(/\s+/g, ' ').trim();
      return [...document.querySelectorAll('table')].map((table) => {
        let headers = [...table.querySelectorAll('thead th')].map((th) => clean(th.textContent));
        if (!headers.length) {
          const firstRow = table.querySelector('tr');
          headers = firstRow ? [...firstRow.children].map((c) => clean(c.textContent)) : [];
        }
        const bodyRows = table.querySelectorAll('tbody tr').length
          ? [...table.querySelectorAll('tbody tr')]
          : [...table.querySelectorAll('tr')].slice(1);
        const rows = bodyRows
          .map((tr) => [...tr.children].map((td) => clean(td.textContent)))
          .filter((cells) => cells.some((c) => c));
        return { headers, rows };
      });
    });
  }

  const MAP_KIND = {
    contracts: 'contract',
    vehicles: 'vehicle',
    bookings: 'booking',
    customers: 'customer',
    ledger: 'ledgerEntry',
  };

  /**
   * قراءة صفحة وتحويل أنسب جدول فيها إلى سجلات التطبيق.
   * عند وجود أكثر من جدول نختار الأعلى تطابقاً مع الحقول المتوقّعة.
   */
  async function readPage(kind, { force = false } = {}) {
    const cached = cache.get(kind);
    if (!force && cached && Date.now() - cached.at < cacheMs) return cached.rows;

    const pages = await discoverPages();
    const target = pages[kind];
    if (!target) {
      throw new HttpError(
        501,
        `لم أعثر على صفحة "${kind}" في لوحتك. عرّفها يدوياً في config/eganis.json تحت browser.pages`,
      );
    }

    const { context: ctx } = await session();
    const page = await ctx.newPage();
    const url = target.href.startsWith('http')
      ? target.href
      : `${config.eganis.baseUrl}${target.href.startsWith('/') ? '' : '/'}${target.href}`;

    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(config.eganis.pageWaitMs);

      if (!(await loggedIn(page))) {
        await autoLogin(page, profile());
        await page.goto(url, { waitUntil: 'domcontentloaded' });
        await page.waitForTimeout(config.eganis.pageWaitMs);
      }

      const tables = await readTables(page);
      const mapKind = MAP_KIND[kind];
      if (!mapKind) return [];

      let best = null;
      for (const table of tables) {
        if (!table.rows.length) continue;
        const { score } = mappingScore(table.headers, mapKind);
        if (!best || score > best.score) best = { ...table, score };
      }

      if (!best || best.score === 0) {
        log.warn(`eganis(browser): لم أفهم جدول صفحة ${kind} (${url})`);
        return [];
      }

      const rows = mapRows(best.headers, best.rows, mapKind);
      cache.set(kind, { at: Date.now(), rows });
      scheduleIdleClose();
      log.debug(`eganis(browser): ${kind} — ${rows.length} سجل`);
      return rows;
    } finally {
      await page.close();
    }
  }

  const filterRows = (rows, filter = {}) => {
    let out = rows;
    if (filter.status) out = out.filter((r) => r.status === filter.status);
    if (filter.branch) out = out.filter((r) => r.branch === filter.branch);
    if (filter.date) {
      out = out.filter((r) =>
        [r.startAt, r.endAt, r.pickupAt, r.at].some((d) => String(d || '').startsWith(filter.date)),
      );
    }
    if (filter.q) {
      const needle = String(filter.q).toLowerCase();
      out = out.filter((r) => JSON.stringify(r).toLowerCase().includes(needle));
    }
    return out;
  };

  const notSupported = (op) => {
    throw new HttpError(
      501,
      `"${op}" يحتاج تنفيذ أمر داخل لوحة eganis — غير مدعوم في وضع المتصفّح بعد. نفّذه من اللوحة مباشرة.`,
    );
  };

  return {
    name: 'browser',

    async health() {
      try {
        await session();
        const pages = await discoverPages();
        const found = Object.keys(pages);
        return {
          ok: found.length > 0,
          driver: 'browser',
          baseUrl: config.eganis.baseUrl,
          pages: found,
          note: found.length ? undefined : 'لم أتعرّف على صفحات اللوحة — عرّفها في config/eganis.json',
        };
      } catch (err) {
        return { ok: false, driver: 'browser', error: err.message };
      }
    },

    /**
     * لقطة لما يراه الخادم في لوحة eganis — للتشخيص من الجوال بلا كمبيوتر:
     * هل وصلنا لصفحة الدخول؟ هل ظهر رمز تحقق؟ هل الجدول فارغ؟
     */
    async screenshot(pathOrKind = '') {
      const { context: ctx } = await session();
      const page = await ctx.newPage();
      try {
        let url = config.eganis.baseUrl;
        if (pathOrKind) {
          const pages = await discoverPages().catch(() => ({}));
          const target = pages[pathOrKind]?.href || pathOrKind;
          url = target.startsWith('http')
            ? target
            : `${config.eganis.baseUrl}${target.startsWith('/') ? '' : '/'}${target}`;
        }
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(config.eganis.pageWaitMs);
        return {
          url: page.url(),
          title: await page.title(),
          loggedIn: await loggedIn(page),
          image: await page.screenshot({ fullPage: true, type: 'png' }),
        };
      } finally {
        await page.close();
      }
    },

    /** إعادة الاكتشاف والقراءة من الصفر — تُستدعى من زر التحديث */
    async refresh() {
      cache.clear();
      discovered = null;
      fs.rmSync(PAGES_CACHE, { force: true });
      return this.health();
    },

    listContracts: async (filter) => filterRows(await readPage('contracts'), filter),
    listVehicles: async (filter) => filterRows(await readPage('vehicles'), filter),
    listBookings: async (filter) => filterRows(await readPage('bookings'), filter),
    async listTasks() {
      // لوحات eganis لا تعرض «مهام» بهذا المعنى؛ نشتقّها من مواعيد العقود والحجوزات
      const [contracts, bookings] = await Promise.all([
        readPage('contracts').catch(() => []),
        readPage('bookings').catch(() => []),
      ]);
      const tasks = [];
      for (const c of contracts) {
        if (c.endAt && c.status !== 'closed') {
          tasks.push({
            id: `ret-${c.no}`,
            type: 'pickup',
            at: c.endAt,
            ref: c.no,
            plate: c.plate,
            driver: null,
            status: 'pending',
          });
        }
      }
      for (const b of bookings) {
        if (b.pickupAt && b.status !== 'cancelled') {
          tasks.push({
            id: `del-${b.no}`,
            type: 'delivery',
            at: b.pickupAt,
            ref: b.no,
            plate: b.plate || null,
            driver: null,
            status: 'pending',
          });
        }
      }
      return tasks;
    },

    async getContract(idOrNo) {
      const rows = await readPage('contracts');
      return rows.find((r) => r.no === idOrNo || r.id === idOrNo) || null;
    },

    async searchCustomers(q) {
      const rows = await readPage('customers').catch(() => []);
      // إن لم توجد صفحة عملاء، نستخرجهم من العقود
      const source = rows.length
        ? rows
        : Object.values(
            (await readPage('contracts')).reduce((acc, c) => {
              const key = c.customerName || c.phone;
              if (key && !acc[key]) {
                acc[key] = { id: key, name: c.customerName, phone: c.phone || null };
              }
              return acc;
            }, {}),
          );
      const needle = String(q || '').toLowerCase();
      if (!needle) return source;
      return source.filter((r) => JSON.stringify(r).toLowerCase().includes(needle));
    },

    async findCustomerByPhone(phone) {
      const digits = String(phone || '').replace(/\D/g, '').slice(-9);
      const rows = await this.searchCustomers('');
      return rows.find((r) => String(r.phone || '').replace(/\D/g, '').endsWith(digits)) || null;
    },

    /** حركات حساب العميل من صفحة «Cari Hesap» إن وُجدت */
    async listLedgerEntries(customerId) {
      const rows = await readPage('ledger').catch(() => []);
      if (!rows.length) return [];
      const needle = String(customerId || '').toLowerCase();
      return rows
        .filter((r) => !needle || JSON.stringify(r).toLowerCase().includes(needle))
        .map((r) => ({
          ...r,
          type: r.direction === 'credit' ? 'payment' : 'extra',
        }));
    },

    extendContract: () => notSupported('تمديد عقد'),
    closeContract: () => notSupported('إغلاق عقد'),
    setVehicleStatus: () => notSupported('تغيير حالة مركبة'),
    assignTask: () => notSupported('إسناد مهمة'),
    completeTask: () => notSupported('إنهاء مهمة'),

    async snapshot() {
      const [vehicles, contracts, bookings, tasks] = await Promise.all([
        this.listVehicles().catch(() => []),
        this.listContracts().catch(() => []),
        this.listBookings().catch(() => []),
        this.listTasks().catch(() => []),
      ]);
      return { today: new Date().toISOString().slice(0, 10), vehicles, contracts, bookings, tasks };
    },

    async close() {
      clearTimeout(idleTimer);
      await context?.close().catch(() => {});
      await browser?.close().catch(() => {});
      context = null;
      browser = null;
    },
  };
}
