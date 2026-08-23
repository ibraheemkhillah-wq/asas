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
import { classifyLink, mapRows, mappingScore, normalizeHeader } from './auto-map.js';

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

/**
 * بناء رابط صفحة داخلية. روابط اللوحة تأتي بثلاث صور: مطلقة، وجذرية تبدأ بـ
 * «/»، ونسبية. `new URL` يتعامل مع الثلاث كما يتعامل معها المتصفّح نفسه،
 * فالجذرية تُبنى على أصل الموقع لا على مسار اللوحة.
 */
function pageUrl(href) {
  const base = config.eganis.baseUrl;
  try {
    return new URL(href, `${base}/`).toString();
  } catch {
    return `${base}${href.startsWith('/') ? '' : '/'}${href}`;
  }
}

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
   * وصف نموذج الدخول كما هو فعلاً: كل حقل باسمه ونوعه ونصّه التوضيحي وعنوانه.
   *
   * هذا ما يُخرجنا من التخمين. لوحة رفضت الدخول ولم تقل سبباً غالباً لم
   * تستلم النموذج أصلاً — إمّا لأن فيها حقلاً ثالثاً (كود الشركة مثلاً) تركناه
   * فارغاً، أو لأن الزر لا يرسل النموذج بل يستدعي جافاسكربت.
   */
  async function describeLoginForm(page) {
    return page
      .evaluate(() => {
        const form = document.querySelector('form:has(input[type="password"])')
          || document.querySelector('form')
          || document.body;

        const labelOf = (el) => {
          if (el.labels?.length) return el.labels[0].textContent;
          if (el.id) return document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.textContent || '';
          return el.closest('label')?.textContent || '';
        };
        const clean = (s) => (s || '').replace(/\s+/g, ' ').trim().slice(0, 40);
        const shown = (el) => !!(el.offsetParent || el.getClientRects().length);

        const fields = [...form.querySelectorAll('input, select, textarea')].map((el) => ({
          tag: el.tagName.toLowerCase(),
          type: (el.getAttribute('type') || 'text').toLowerCase(),
          name: clean(el.getAttribute('name')),
          id: clean(el.id),
          placeholder: clean(el.getAttribute('placeholder')),
          label: clean(labelOf(el)),
          required: el.required,
          visible: shown(el),
          filled: !!el.value,
        }));

        const buttons = [...form.querySelectorAll('button, input[type="submit"], a.btn')].map((el) => ({
          tag: el.tagName.toLowerCase(),
          type: clean(el.getAttribute('type')),
          text: clean(el.textContent || el.value),
          onclick: !!el.getAttribute('onclick'),
        }));

        // أي نص ظاهر يشبه رسالة رفض، ولو لم يكن في حاوية معروفة
        const words = /(hatal|yanlış|yanlis|geçersiz|gecersiz|hata|zorunlu|boş|bos|doğrula|dogrula|kilitli|başarısız|basarisiz)/i;
        const notes = [...form.querySelectorAll('span, div, p, li, label')]
          .filter((el) => shown(el) && el.children.length === 0 && words.test(el.textContent || ''))
          .map((el) => clean(el.textContent))
          .filter(Boolean);

        return {
          action: clean(form.getAttribute?.('action')) || '(بلا action)',
          method: clean(form.getAttribute?.('method')) || 'GET',
          fields,
          buttons,
          notes: [...new Set(notes)].slice(0, 4),
        };
      })
      .catch(() => null);
  }

  /** سطر واحد مقروء يصف النموذج، يُوضع في السجل */
  function formSummary(info) {
    if (!info) return 'تعذّر قراءة النموذج';
    const field = (f) =>
      `${f.name || f.id || '?'}[${f.type}]${f.required ? '*' : ''}${f.filled ? '=مُعبّأ' : ''}`;
    const visible = info.fields.filter((f) => f.visible && f.type !== 'hidden');
    const parts = [
      `النموذج: ${info.method} ${info.action}`,
      `الحقول الظاهرة (${visible.length}): ${visible.map(field).join(' · ') || 'لا شيء'}`,
      `الأزرار: ${info.buttons.map((b) => `«${b.text}»[${b.type || 'بلا نوع'}${b.onclick ? '+js' : ''}]`).join(' · ') || 'لا شيء'}`,
    ];
    if (info.notes.length) parts.push(`ملاحظات الصفحة: ${info.notes.join(' · ')}`);
    return parts.join(' | ');
  }

  /*
   * ترجيح حقل اسم المستخدم بالكلمات التي تحيط به، لا بترتيبه في الصفحة.
   * لوحات تركية كثيرة تسبق حقل المستخدم بحقل «كود الشركة»، فلو أخذنا الأول
   * كتبنا البريد في الكود وأرسلنا النموذج ناقصاً — فيُرفض بلا رسالة.
   */
  const USER_WORDS = /(kullanici|kullanıcı|user|email|e-?posta|eposta|mail|login|giris|giriş|adi|adı)/i;
  const NOT_USER_WORDS = /(firma|şirket|sirket|company|kod|code|captcha|guvenlik|güvenlik|dogrula|doğrula|ara|search|sube|şube)/i;

  function scoreUserField(f) {
    const hay = `${f.name} ${f.id} ${f.placeholder} ${f.label}`;
    let score = 0;
    if (USER_WORDS.test(hay)) score += 3;
    if (NOT_USER_WORDS.test(hay)) score -= 4;
    if (f.type === 'email') score += 2;
    if (f.required) score += 1;
    return score;
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

    // وصف النموذج قبل أي كتابة — نحتاجه للتشخيص إن فشل الدخول
    const before = await describeLoginForm(page);

    /*
     * حقل اسم المستخدم: المحدَّد يدوياً، وإلا أفضل مرشّح بالكلمات المحيطة
     * داخل النموذج الحاوي لكلمة السر. مربّع البحث في الترويسة أو حقل «كود
     * الشركة» يخرجان بالترجيح السالب.
     */
    const formScope = page.locator('form:has(input[type="password"])').first();
    const hasForm = (await formScope.count().catch(() => 0)) > 0;
    const scope = hasForm ? formScope : page;
    const TEXT_INPUTS = 'input[type="text"], input[type="email"], input[type="tel"], input:not([type])';

    let userField;
    if (spec.usernameSelector) {
      userField = page.locator(spec.usernameSelector);
    } else {
      const candidates = (before?.fields || []).filter(
        (f) => f.tag === 'input' && f.visible && ['text', 'email', 'tel'].includes(f.type),
      );
      const best = candidates
        .map((f, i) => ({ f, i, score: scoreUserField(f) }))
        .sort((a, b) => b.score - a.score || a.i - b.i)[0];

      userField =
        best && best.score > 0 && best.f.name
          ? scope.locator(`input[name="${best.f.name}"]`).first()
          : scope.locator(TEXT_INPUTS).filter({ visible: true }).first();

      // حقول نصية ظاهرة أكثر من واحد = اللوحة تطلب شيئاً زائداً عن الاسم
      if (candidates.length > 1) {
        log.warn(
          `eganis(browser): نموذج الدخول فيه ${candidates.length} حقول نصية — ` +
            `اخترت «${best?.f.name || best?.f.placeholder || '?'}» لاسم المستخدم`,
        );
      }
    }

    await userField.fill(username);
    await passwordField.fill(password);

    const submitInForm = scope
      .locator('button[type="submit"], input[type="submit"], button:not([type])')
      .filter({ visible: true })
      .first();

    const submit = spec.submitSelector
      ? page.locator(spec.submitSelector)
      : (await submitInForm.count().catch(() => 0))
        ? submitInForm
        : page
            .locator('button[type="submit"], input[type="submit"], button:has-text("Giriş"), button:has-text("Login")')
            .first();

    const urlBefore = page.url();

    // نافذة تنبيه جافاسكربت تُجمّد الصفحة إن لم تُغلق، ونصّها هو سبب الرفض
    let dialogText = '';
    page.on('dialog', (dialog) => {
      dialogText = dialog.message().replace(/\s+/g, ' ').trim().slice(0, 200);
      dialog.dismiss().catch(() => {});
    });

    await Promise.all([
      page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {}),
      submit.click({ timeout: 15000 }).catch(() => {}),
    ]);
    await page.waitForTimeout(1500);

    // بعض النماذج لا تستجيب للنقر على الزر بل لمفتاح الإدخال
    if (!(await loggedIn(page))) {
      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {}),
        passwordField.press('Enter').catch(() => {}),
      ]);
      await page.waitForTimeout(1500);
    }

    // آخر محاولة: إرسال النموذج برمجياً، لتخطّي زر يعتمد على جافاسكربت معطّل
    if (!(await loggedIn(page)) && hasForm && page.url() === urlBefore) {
      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 20000 }).catch(() => {}),
        page
          .evaluate(() => {
            const form = document.querySelector('form:has(input[type="password"])');
            if (form) HTMLFormElement.prototype.submit.call(form);
          })
          .catch(() => {}),
      ]);
      await page.waitForTimeout(1500);
    }

    if (!(await loggedIn(page))) {
      // اللوحة نفسها تقول سبب الرفض عادةً — ننقله بدل رسالة عامة
      const panelMessage = await page
        .evaluate(() => {
          const selectors = [
            '.validation-summary-errors', '.field-validation-error', '.alert-danger',
            '.alert-error', '.text-danger', '[role="alert"]', '.error-message', '.invalid-feedback',
            '.toast-message', '.swal2-html-container', '#toast-container',
          ].join(', ');
          const texts = [...document.querySelectorAll(selectors)]
            .map((node) => (node.textContent || '').replace(/\s+/g, ' ').trim())
            .filter(Boolean);
          return [...new Set(texts)].join(' · ').slice(0, 250);
        })
        .catch(() => '');

      const after = await describeLoginForm(page);
      const moved = page.url() !== urlBefore;

      // نذكر اسم المستخدم وطول كلمة السر (لا قيمتها) ليتبيّن الخطأ المطبعي
      const hint =
        `المستخدم: ${username} · كلمة السر: ${password.length} حرفاً · ` +
        `الصفحة: ${page.url()} · ${moved ? 'انتقلت الصفحة بعد الإرسال' : 'الصفحة لم تتغيّر بعد الإرسال'}`;

      const reason = panelMessage || dialogText || after?.notes?.join(' · ') || '';

      // بنية النموذج تُغني عن لقطة الشاشة: تُظهر أي حقل مطلوب بقي فارغاً
      log.warn(`eganis(browser): ${formSummary(after || before)}`);

      throw new HttpError(
        401,
        reason
          ? `فشل تسجيل الدخول — رسالة اللوحة: «${reason}» (${hint})`
          : `فشل تسجيل الدخول ولم تُظهر اللوحة سبباً. راجع سطر «النموذج» في السجل (${hint})`,
      );
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
      try {
        await autoLogin(page, spec);
      } catch (err) {
        // جلسة محفوظة تالفة تُفشل كل محاولة تالية — نتخلّص منها فوراً
        if (fs.existsSync(sessionFile)) {
          fs.rmSync(sessionFile, { force: true });
          log.warn('eganis(browser): حُذفت الجلسة المحفوظة بعد فشل الدخول');
        }
        throw err;
      }
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

  /** قراءة كل روابط اللوحة — أساس الاكتشاف التلقائي والاختيار اليدوي */
  async function panelLinks() {
    const { context: ctx } = await session();
    const page = await ctx.newPage();
    try {
      await page.goto(config.eganis.baseUrl, { waitUntil: 'domcontentloaded' });
      await page.waitForTimeout(config.eganis.pageWaitMs);

      // كثير من اللوحات تُخفي القوائم خلف أزرار — نفتحها قبل القراءة
      for (const selector of ['.dropdown-toggle', '[data-toggle="collapse"]', '.nav-link.has-arrow']) {
        const toggles = await page.locator(selector).all().catch(() => []);
        for (const toggle of toggles.slice(0, 20)) {
          await toggle.click({ timeout: 1200 }).catch(() => {});
        }
      }
      await page.waitForTimeout(600);

      const links = await page.$$eval('a[href]', (nodes) =>
        nodes
          .map((a) => ({
            text: (a.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 60),
            href: a.getAttribute('href'),
          }))
          .filter((l) => l.href && !l.href.startsWith('javascript') && l.href !== '#'),
      );
      const seen = new Set();
      return links.filter((l) => !seen.has(l.href) && seen.add(l.href));
    } finally {
      await page.close();
      scheduleIdleClose();
    }
  }

  /** الصفحات التي اختارها المستخدم بنفسه من شاشة الإعدادات */
  function manualPages() {
    const raw = config.eganis.pages;
    if (!raw) return null;
    try {
      const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw;
      const entries = Object.entries(parsed).filter(([, href]) => href);
      if (!entries.length) return null;
      return Object.fromEntries(entries.map(([kind, href]) => [kind, { href, manual: true }]));
    } catch {
      return null;
    }
  }

  /** اكتشاف صفحات اللوحة مرة واحدة، مع تخزينها لتسريع الإقلاع لاحقاً */
  async function discoverPages() {
    if (discovered) return discovered;

    // اختيار المستخدم أولاً — هو الأدرى بلوحته
    const chosen = manualPages();
    if (chosen) {
      discovered = chosen;
      return discovered;
    }

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

    const links = await panelLinks();
    const found = {};
    for (const link of links) {
      const kind = classifyLink(link);
      if (kind && !found[kind]) found[kind] = { href: link.href, text: link.text };
    }
    discovered = found;

    try {
      fs.mkdirSync(path.dirname(PAGES_CACHE), { recursive: true });
      fs.writeFileSync(PAGES_CACHE, JSON.stringify(found, null, 2), 'utf8');
    } catch {
      /* بلا قرص دائم — نكتفي بالذاكرة */
    }
    log.info(`eganis(browser): اكتُشفت الصفحات — ${Object.keys(found).join(', ') || 'لا شيء'}`);
    return discovered;
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

  /** روابط لا تحوي بيانات تشغيل — نوفّر وقت فحصها */
  const SKIP_WORDS = [
    'cikis', 'logout', 'ayarlar', 'profil', 'hesabim', 'yardim', 'destek',
    'sifre', 'password', 'kullanici', 'yetki', 'log', 'bildirim', 'hakkinda',
  ];

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
        `لم أعثر على صفحة "${kind}" في لوحتك — اختَرها يدوياً من شاشة الإعدادات`,
      );
    }

    const { context: ctx } = await session();
    const page = await ctx.newPage();
    const url = pageUrl(target.href);

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
     * اكتشاف الصفحات بفحص محتواها لا بأسمائها.
     *
     * أسماء القوائم تختلف بين تركيبات eganis، لكن **أعمدة الجداول ثابتة**:
     * صفحة فيها «Sözleşme No · Müşteri · Plaka» هي العقود مهما سُمّيت.
     * فنزور الصفحات واحدة واحدة ونحكم على كل واحدة من ترويسة جدولها.
     */
    async autodetect({ limit = 16, onProgress } = {}) {
      const links = await panelLinks();
      const base = config.eganis.baseUrl;

      const candidates = links
        .filter((link) => {
          const hay = normalizeHeader(`${link.text} ${link.href}`);
          if (!hay) return false;
          if (SKIP_WORDS.some((word) => hay.includes(word))) return false;
          if (/^https?:\/\//i.test(link.href) && !link.href.startsWith(base)) return false;
          return true;
        })
        .slice(0, limit);

      const { context: ctx } = await session();
      const kinds = Object.entries(MAP_KIND);
      const examined = []; // كل جدول وجدناه ودرجات مطابقته لكل نوع

      for (const [index, link] of candidates.entries()) {
        onProgress?.({ index: index + 1, total: candidates.length, text: link.text || link.href });

        const url = pageUrl(link.href);
        const page = await ctx.newPage();
        try {
          await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
          await page.waitForTimeout(config.eganis.pageWaitMs);

          for (const table of await readTables(page)) {
            if (!table.rows.length) continue;
            const scores = {};
            for (const [kind, mapKind] of kinds) scores[kind] = mappingScore(table.headers, mapKind);
            examined.push({ link, rows: table.rows.length, scores });
          }
        } catch (err) {
          log.debug(`eganis(browser): تعذّر فحص ${url} — ${err.message}`);
        } finally {
          await page.close();
        }
      }

      /**
       * كل صفحة شيء واحد لا عدّة أشياء.
       *
       * جدول العقود يحوي «Plaka» و«Müşteri»، فلو حكمنا على كل نوع وحده لظنناه
       * صفحة مركبات وصفحة عملاء أيضاً. لذا نسأل أولاً: هذا الجدول أقرب ما يكون
       * إلى ماذا؟ (أعلى درجة، ثم أكثر الحقول تطابقاً)، ثم نوزّع الأنواع عليها.
       */
      const primaryOf = (entry) =>
        kinds
          .map(([kind]) => ({ kind, ...entry.scores[kind] }))
          .sort((a, b) => b.score - a.score || b.matched - a.matched)[0];

      const found = {};
      const claimed = new Set();

      for (const [kind] of kinds) {
        const best = examined
          .filter((e) => !claimed.has(e) && primaryOf(e).kind === kind && e.scores[kind].score >= 0.6)
          .sort((a, b) => b.scores[kind].score - a.scores[kind].score || b.rows - a.rows)[0];
        if (best) {
          claimed.add(best);
          found[kind] = {
            href: best.link.href,
            text: best.link.text,
            score: best.scores[kind].score,
            rows: best.rows,
          };
        }
      }

      // نوع لم تُخصَّص له صفحة: نقبل أفضل مطابقة ثانوية من صفحة غير مأخوذة
      for (const [kind] of kinds) {
        if (found[kind]) continue;
        const best = examined
          .filter((e) => !claimed.has(e) && e.scores[kind].score >= 0.6)
          .sort((a, b) => b.scores[kind].score - a.scores[kind].score || b.rows - a.rows)[0];
        if (best) {
          claimed.add(best);
          found[kind] = {
            href: best.link.href,
            text: best.link.text,
            score: best.scores[kind].score,
            rows: best.rows,
            secondary: true,
          };
        }
      }

      scheduleIdleClose();
      if (Object.keys(found).length) {
        discovered = found;
        try {
          fs.mkdirSync(path.dirname(PAGES_CACHE), { recursive: true });
          fs.writeFileSync(PAGES_CACHE, JSON.stringify(found, null, 2), 'utf8');
        } catch {
          /* بلا قرص دائم */
        }
      }
      return { found, scanned: candidates.length };
    },

    /** كل روابط اللوحة مع تخمين نوع كل واحد — لاختيار الصفحات يدوياً */
    async links() {
      const found = await panelLinks();
      return found.map((link) => ({ ...link, guess: classifyLink(link) }));
    },

    /**
     * لقطة لما يراه الخادم في لوحة eganis — للتشخيص من الجوال بلا كمبيوتر:
     * هل وصلنا لصفحة الدخول؟ هل ظهر رمز تحقق؟ هل الجدول فارغ؟
     */
    /**
     * تشخيص الدخول بالنص: ماذا يطلب نموذج اللوحة فعلاً، وهل نجح الدخول.
     * أخفّ من الصورة وأوضح للقراءة من الجوال.
     */
    async loginDiagnose() {
      const started = Date.now();
      try {
        const { context: ctx } = await session();
        const page = await ctx.newPage();
        try {
          return {
            ok: true,
            url: config.eganis.baseUrl,
            user: config.eganis.username,
            passwordLength: config.eganis.password.length,
            title: await page.title().catch(() => ''),
            tookMs: Date.now() - started,
          };
        } finally {
          await page.close();
        }
      } catch (err) {
        // افتح صفحة الدخول نظيفةً واقرأ بنيتها — هذا ما يكشف الحقل الناقص
        let form = null;
        let title = '';
        const fresh = await launchBrowser().catch(() => null);
        if (fresh) {
          const ctx = await fresh.newContext({ locale: 'tr-TR' });
          const page = await ctx.newPage();
          try {
            await page.goto(config.eganis.baseUrl, { waitUntil: 'domcontentloaded', timeout: 45000 });
            await page.waitForTimeout(config.eganis.pageWaitMs);
            title = await page.title().catch(() => '');
            form = await describeLoginForm(page);
          } catch {
            /* نكتفي بما جمعناه */
          } finally {
            await page.close().catch(() => {});
            await ctx.close().catch(() => {});
            if (fresh !== browser) await fresh.close().catch(() => {});
          }
        }
        return {
          ok: false,
          error: err.message,
          url: config.eganis.baseUrl,
          user: config.eganis.username,
          passwordLength: config.eganis.password.length,
          title,
          form,
          summary: formSummary(form),
          tookMs: Date.now() - started,
        };
      }
    },

    async screenshot(pathOrKind = '') {
      let ctx;
      let loginError = '';
      try {
        ({ context: ctx } = await session());
      } catch (err) {
        /*
         * فشل الدخول هو أكثر لحظة نحتاج فيها لقطة الشاشة، فلا يصحّ أن تمنعها.
         * نفتح متصفّحاً بلا جلسة ونصوّر صفحة الدخول كما هي.
         */
        loginError = err.message;
        browser = browser || (await launchBrowser());
        ctx = await browser.newContext({ locale: 'tr-TR' });
      }

      const page = await ctx.newPage();
      try {
        let url = config.eganis.baseUrl;
        if (pathOrKind && !loginError) {
          const pages = await discoverPages().catch(() => ({}));
          url = pageUrl(pages[pathOrKind]?.href || pathOrKind);
        }
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
        await page.waitForTimeout(config.eganis.pageWaitMs);
        return {
          url: page.url(),
          title: await page.title(),
          loggedIn: await loggedIn(page),
          loginError: loginError || undefined,
          form: loginError ? formSummary(await describeLoginForm(page)) : undefined,
          image: await page.screenshot({ fullPage: true, type: 'png' }),
        };
      } finally {
        await page.close();
        if (loginError) await ctx.close().catch(() => {});
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
