/**
 * سائق eganis عبر أتمتة المتصفح (Playwright).
 *
 * يُستخدم عندما لا يتوفّر Web Service: يسجّل الدخول إلى واجهة eganis
 * ويقرأ الجداول حسب المحدِّدات (selectors) المعرّفة في config/eganis.json
 * تحت المفتاح "browser".
 *
 * التثبيت (اختياري):  npm i playwright && npx playwright install chromium
 */
import fs from 'node:fs';
import path from 'node:path';
import { config } from '../../config.js';
import { HttpError } from '../../lib/http.js';
import { log } from '../../lib/log.js';

let chromium = null;

async function loadPlaywright() {
  if (chromium) return chromium;
  try {
    ({ chromium } = await import('playwright'));
    return chromium;
  } catch {
    throw new HttpError(
      500,
      'حزمة playwright غير مثبّتة. نفّذ: npm i playwright && npx playwright install chromium',
    );
  }
}

function browserProfile() {
  const file = path.resolve(process.cwd(), config.eganis.endpointsFile);
  if (!fs.existsSync(file)) {
    throw new HttpError(500, `ملف تعريف eganis غير موجود: ${file}`);
  }
  const profile = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!profile.browser) {
    throw new HttpError(500, 'القسم "browser" غير معرّف في ملف تعريف eganis');
  }
  return profile.browser;
}

export function createBrowserDriver() {
  let browser = null;
  let context = null;

  async function session() {
    const spec = browserProfile();
    if (context) return { context, spec };
    const engine = await loadPlaywright();
    browser = await engine.launch({ headless: true });
    context = await browser.newContext({ locale: 'ar' });
    const page = await context.newPage();
    log.info('eganis(browser): تسجيل الدخول…');
    await page.goto(`${config.eganis.baseUrl}${spec.loginPath || '/'}`, { waitUntil: 'domcontentloaded' });
    await page.fill(spec.usernameSelector, config.eganis.username);
    await page.fill(spec.passwordSelector, config.eganis.password);
    await Promise.all([
      page.waitForLoadState('networkidle').catch(() => {}),
      page.click(spec.submitSelector),
    ]);
    await page.close();
    return { context, spec };
  }

  /** قراءة جدول HTML وتحويله إلى كائنات حسب ترتيب الأعمدة */
  async function scrapeTable(pagePath, tableSelector, columns) {
    const { context: ctx } = await session();
    const page = await ctx.newPage();
    try {
      await page.goto(`${config.eganis.baseUrl}${pagePath}`, { waitUntil: 'networkidle' });
      await page.waitForSelector(tableSelector, { timeout: 15000 });
      const rows = await page.$$eval(`${tableSelector} tbody tr`, (trs) =>
        trs.map((tr) => Array.from(tr.querySelectorAll('td')).map((td) => td.innerText.trim())),
      );
      return rows.map((cells) => {
        const record = {};
        columns.forEach((name, index) => {
          if (name) record[name] = cells[index] ?? null;
        });
        return record;
      });
    } finally {
      await page.close();
    }
  }

  const notSupported = (op) => {
    throw new HttpError(
      501,
      `العملية "${op}" غير مدعومة في وضع المتصفح — استخدم EGANIS_DRIVER=api أو أضِف تعريفاً لها`,
    );
  };

  return {
    name: 'browser',

    async health() {
      try {
        await session();
        return { ok: true, driver: 'browser', baseUrl: config.eganis.baseUrl };
      } catch (err) {
        return { ok: false, driver: 'browser', error: err.message };
      }
    },

    async listVehicles() {
      const spec = browserProfile();
      const page = spec.pages?.vehicles;
      if (!page) return notSupported('listVehicles');
      return scrapeTable(page.path, page.table, page.columns);
    },

    async listContracts() {
      const spec = browserProfile();
      const page = spec.pages?.contracts;
      if (!page) return notSupported('listContracts');
      return scrapeTable(page.path, page.table, page.columns);
    },

    async listBookings() {
      const spec = browserProfile();
      const page = spec.pages?.bookings;
      if (!page) return notSupported('listBookings');
      return scrapeTable(page.path, page.table, page.columns);
    },

    async listTasks() {
      const spec = browserProfile();
      const page = spec.pages?.tasks;
      if (!page) return notSupported('listTasks');
      return scrapeTable(page.path, page.table, page.columns);
    },

    async getContract(id) {
      const rows = await this.listContracts();
      return rows.find((r) => r.no === id || r.id === id) || null;
    },
    async searchCustomers(q) {
      const spec = browserProfile();
      const page = spec.pages?.customers;
      if (!page) return notSupported('searchCustomers');
      const rows = await scrapeTable(page.path, page.table, page.columns);
      const needle = String(q || '').toLowerCase();
      return rows.filter((r) => JSON.stringify(r).toLowerCase().includes(needle));
    },
    async findCustomerByPhone(phone) {
      const rows = await this.searchCustomers(phone);
      return rows[0] || null;
    },

    extendContract: () => notSupported('extendContract'),
    closeContract: () => notSupported('closeContract'),
    setVehicleStatus: () => notSupported('setVehicleStatus'),
    assignTask: () => notSupported('assignTask'),
    completeTask: () => notSupported('completeTask'),

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
      await context?.close();
      await browser?.close();
      context = null;
      browser = null;
    },
  };
}
