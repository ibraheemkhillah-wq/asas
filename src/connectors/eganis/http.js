/**
 * سائق eganis بلا متصفّح — يعمل بحسابك العادي، وبذاكرة عشرات الميجابايتات.
 *
 * لماذا لا متصفّح؟ لأن Chromium وحده يتجاوز نصف جيجابايت أحياناً، فتسقط
 * الاستضافة الصغيرة ويتوقّف التطبيق كلّه (502). ولوحة eganis صفحات
 * ASP.NET عادية: نسجّل الدخول بإرسال النموذج، ونحتفظ بالكوكيز، ونقرأ
 * الجداول من نصّ الصفحة. أسرع وأخفّ وأقلّ عطباً.
 *
 * ما يبقى للمتصفّح: الصفحات التي تُبنى بجافاسكربت فقط. إن ظهرت، يقول
 * التطبيق ذلك صراحةً ويمكن التحويل إلى وضع `browser`.
 */
import fs from 'node:fs';
import path from 'node:path';
import { config } from '../../config.js';
import { HttpError } from '../../lib/http.js';
import { log } from '../../lib/log.js';
import { arabicKeyboardToLatin, describeValue } from '../../lib/keyboard.js';
import { classifyLink, mapRows, mappingScore, normalizeHeader } from './auto-map.js';
import {
  analyzeLoginScripts,
  extractErrors,
  extractLinks,
  extractTables,
  findLoginForm,
  looksLikeLogin,
  textOf,
} from './html.js';

const UA =
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
  'Chrome/124.0.0.0 Safari/537.36';

/** مرطبان كوكيز بسيط: اللوحة تحتاج كوكي الجلسة وكوكي مانع التزوير */
class CookieJar {
  constructor() {
    this.map = new Map();
  }

  absorb(response) {
    const raw = response.headers.getSetCookie?.() || [];
    for (const line of raw) {
      const [pair] = line.split(';');
      const eq = pair.indexOf('=');
      if (eq === -1) continue;
      const name = pair.slice(0, eq).trim();
      const value = pair.slice(eq + 1).trim();
      // قيمة فارغة = طلبٌ بالحذف
      if (!value || /expires=Thu, 01 Jan 1970/i.test(line)) this.map.delete(name);
      else this.map.set(name, value);
    }
  }

  header() {
    return [...this.map].map(([k, v]) => `${k}=${v}`).join('; ');
  }

  get size() {
    return this.map.size;
  }

  clear() {
    this.map.clear();
  }
}

export function createHttpDriver() {
  const jar = new CookieJar();
  let loggedIn = false;
  let discovered = null;
  const cache = new Map(); // kind → { at, rows }
  const cacheMs = Math.max(0, config.eganis.cacheSeconds) * 1000;

  const PAGES_CACHE = path.resolve(process.cwd(), 'data/eganis-pages.json');

  function base() {
    if (!config.eganis.baseUrl) throw new HttpError(500, 'EGANIS_BASE_URL غير محدّد');
    return config.eganis.baseUrl;
  }

  /** الروابط الجذرية تُحلّ على أصل الموقع، والنسبية على مسار اللوحة */
  function resolve(href, from = `${base()}/`) {
    try {
      return new URL(href, from).toString();
    } catch {
      return `${base()}${String(href).startsWith('/') ? '' : '/'}${href}`;
    }
  }

  /**
   * طلب واحد مع متابعة التحويلات يدوياً — الكوكيز تُحقن في كل قفزة، وهذا
   * ما لا تفعله المتابعة التلقائية فتضيع الجلسة بين تحويل وآخر.
   */
  async function request(url, { method = 'GET', body, referer } = {}) {
    const trail = [];
    let current = url;

    for (let hop = 0; hop < 6; hop += 1) {
      const headers = {
        'User-Agent': UA,
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        Accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        ...(jar.size ? { Cookie: jar.header() } : {}),
        ...(referer ? { Referer: referer } : {}),
        ...(hop === 0 && body ? { 'Content-Type': 'application/x-www-form-urlencoded' } : {}),
      };

      const response = await fetch(current, {
        method: hop === 0 ? method : 'GET',
        headers,
        body: hop === 0 ? body : undefined,
        redirect: 'manual',
        signal: AbortSignal.timeout(config.eganis.timeoutMs),
      });

      jar.absorb(response);
      const location = response.headers.get('location');
      trail.push(`${hop === 0 ? method : 'GET'} ${short(current)} → ${response.status}`);

      if (response.status >= 300 && response.status < 400 && location) {
        current = resolve(location, current);
        continue;
      }

      const html = await response.text();
      return { url: current, status: response.status, html, trail };
    }

    throw new HttpError(502, `تحويلات كثيرة من اللوحة: ${trail.join(' ← ')}`);
  }

  function short(url) {
    try {
      const { pathname, search } = new URL(url);
      return (pathname + search).slice(0, 60);
    } catch {
      return String(url).slice(0, 60);
    }
  }

  // ===== تسجيل الدخول =====

  const USER_WORDS = /(kullanici|kullanıcı|user|email|e-?posta|eposta|mail|login|giris|giriş|adi|adı)/i;
  const NOT_USER = /(firma|şirket|sirket|company|kod|code|captcha|guvenlik|güvenlik|ara|search|sube|şube)/i;

  /** ترجيح حقل اسم المستخدم بالكلمات المحيطة به لا بترتيبه */
  function pickUserField(form) {
    const candidates = form.fields.filter(
      (f) => ['text', 'email', 'tel'].includes(f.type) && f.name,
    );
    if (!candidates.length) return null;

    const labelFor = (f) => form.labels.find((l) => l.forId && l.forId === f.id)?.text || '';
    const scored = candidates.map((f, i) => {
      const hay = `${f.name} ${f.id} ${f.placeholder} ${labelFor(f)}`;
      let score = 0;
      if (USER_WORDS.test(hay)) score += 3;
      if (NOT_USER.test(hay)) score -= 4;
      if (f.type === 'email') score += 2;
      if (f.required) score += 1;
      return { f, i, score };
    });

    scored.sort((a, b) => b.score - a.score || a.i - b.i);
    return { field: scored[0].f, ambiguous: candidates.length > 1, candidates: candidates.length };
  }

  /** وصف النموذج بسطر واحد — يُظهر أي حقل تطلبه اللوحة وتركناه فارغاً */
  function formSummary(form) {
    if (!form) return 'لا يوجد نموذج دخول في الصفحة';
    const visible = form.fields.filter((f) => f.type !== 'hidden');
    const one = (f) => `${f.name || f.id || '?'}[${f.type}]${f.required ? '*' : ''}`;
    return (
      `النموذج: ${form.method} ${form.action || '(نفس الصفحة)'} | ` +
      `الحقول (${visible.length}): ${visible.map(one).join(' · ') || 'لا شيء'} | ` +
      `المخفية: ${form.fields.filter((f) => f.type === 'hidden').map((f) => f.name).join(' · ') || 'لا شيء'}`
    );
  }

  /** وصف شكل القيمة بلا كشفها — لالتقاط أخطاء الإدخال والنسخ */
  const valueShape = (value) => describeValue(value).text;

  /*
   * تهدئة بعد الفشل — حماية للحساب لا للتطبيق.
   *
   * التطبيق يفتح صفحات ويفحص حالته باستمرار، وكل واحدة تستدعي دخولاً. فإن
   * كانت البيانات خاطئة تحوّلت هذه إلى عشرات المحاولات الفاشلة في الدقيقة،
   * وأنظمة ASP.NET تقفل الحساب بعد خمس محاولات. عندها يصير القفل نفسه هو
   * سبب الفشل، فلا تنجح البيانات الصحيحة حين تُصحَّح.
   *
   * فبعد كل فشل ننتظر — دقيقة، ثم دقيقتين، حتى خمس — ونعيد الخطأ الأخير بدل
   * طرق الباب. وأي حفظ لإعدادات جديدة يمسح التهدئة فوراً (resetEganis).
   */
  let failures = 0;
  let blockedUntil = 0;
  let lastError = null;
  // المتصفّح يُجرَّب مرة واحدة لكل دورة تهدئة، لا عند كل محاولة
  let browserTried = false;
  /*
   * لوحة ثبت أنها تحتاج متصفّحاً لا نعيد عليها الإرسال الخام. ليس توفيراً
   * للوقت فحسب: كل محاولة فاشلة تُقرَّب الحساب من القفل، ونحن نعرف سلفاً
   * أنها ستفشل.
   */
  let preferBrowserLogin = false;
  // آخر لقطة التُقطت أثناء فشل دخول بالمتصفّح — تُعرض في شاشة الإعدادات
  let lastLoginShot = null;

  const cooldownMs = () => Math.min(5, failures) * 60000;

  async function login() {
    const { username, password } = config.eganis;
    if (!username || !password) {
      throw new HttpError(401, 'بيانات دخول eganis غير مضبوطة (EGANIS_USERNAME و EGANIS_PASSWORD)');
    }

    if (Date.now() < blockedUntil) {
      const seconds = Math.ceil((blockedUntil - Date.now()) / 1000);
      throw new HttpError(
        401,
        `${lastError} — توقّفت المحاولات ${seconds} ثانية حمايةً لحسابك من القفل. ` +
          'صحّح البيانات في شاشة الإعدادات وسأحاول فوراً.',
      );
    }

    jar.clear();
    const landing = await request(base());
    const form = findLoginForm(landing.html);

    if (!form) {
      // لا نموذج ولا كلمة سر = نحن داخل اللوحة أصلاً (نادر لكنه ممكن)
      if (!looksLikeLogin(landing.html)) {
        loggedIn = true;
        return landing;
      }
      throw new HttpError(
        401,
        `لم أجد نموذج دخول في ${landing.url} — قد تكون الصفحة تُبنى بجافاسكربت. ` +
          'جرّب وضع browser إن كانت الاستضافة تحتمله.',
      );
    }

    const passwordField = form.fields.find((f) => f.type === 'password');
    const picked = pickUserField(form);
    if (!picked) {
      throw new HttpError(401, `نموذج الدخول بلا حقل اسم مستخدم — ${formSummary(form)}`);
    }
    // لوحة نعرف أنها تحتاج متصفّحاً: لا نُهدر عليها محاولة فاشلة مؤكّدة
    if (preferBrowserLogin && config.eganis.loginViaBrowser !== 'never') {
      return loginViaBrowser({ userName: picked.field.name, passwordName: passwordField.name });
    }

    if (picked.ambiguous) {
      log.warn(
        `eganis(http): نموذج الدخول فيه ${picked.candidates} حقول نصية — ` +
          `اخترت «${picked.field.name}» لاسم المستخدم`,
      );
    }

    /*
     * نرسل كل حقول النموذج كما وجدناها — ومنها __RequestVerificationToken
     * الذي ترفض ASP.NET الطلب بدونه — ثم نستبدل الاسم وكلمة السر.
     */
    const body = new URLSearchParams();
    for (const f of form.fields) {
      if (!f.name) continue;
      if (['submit', 'button', 'image', 'reset'].includes(f.type)) continue;
      if (['checkbox', 'radio'].includes(f.type) && !f.checked) continue;
      body.set(f.name, f.value || '');
    }
    body.set(picked.field.name, username);
    body.set(passwordField.name, password);

    const action = form.action ? resolve(form.action, landing.url) : landing.url;
    const result = await request(action, {
      method: form.method === 'GET' ? 'GET' : 'POST',
      body: body.toString(),
      referer: landing.url,
    });

    if (!looksLikeLogin(result.html)) {
      loggedIn = true;
      failures = 0;
      blockedUntil = 0;
      lastError = null;
      log.info('eganis(http): تم تسجيل الدخول');
      return result;
    }

    // فشل — نقول السبب بلسان اللوحة، وإلا نصف ما حدث بدقّة
    loggedIn = false;
    const panelErrors = extractErrors(result.html);
    const gotCookies = jar.size > 0;

    log.warn(`eganis(http): ${formSummary(form)}`);
    log.warn(`eganis(http): الطلبات: ${result.trail.join(' ← ')} · الكوكيز: ${jar.size}`);

    /*
     * الإرسال الخام فشل. قبل أن نتّهم كلمة السر، نسأل الصفحة نفسها: هل
     * جافاسكربت يعبث بالنموذج قبل الإرسال؟ إن كان كذلك فلا ذنب للبيانات،
     * والحلّ أن يقوم متصفّح حقيقي بالمصافحة مرّة ثم نكمل نحن.
     */
    const scripts = analyzeLoginScripts(landing.html, form);
    if (config.eganis.loginViaBrowser !== 'never' && !browserTried) {
      browserTried = true;
      if (scripts.needsBrowser || config.eganis.loginViaBrowser === 'always') {
        log.warn(
          'eganis(http): نموذج الدخول يعالَج بجافاسكربت' +
            `${scripts.cryptoHints.length ? ` (${scripts.cryptoHints.join(', ')})` : ''}` +
            ' — أنتقل إلى الدخول عبر المتصفّح',
        );
        try {
          return await loginViaBrowser({
            userName: picked.field.name,
            passwordName: passwordField.name,
          });
        } catch (err) {
          log.warn(`eganis(http): الدخول عبر المتصفّح فشل — ${err.message}`);
          lastError = err.message;
          failures += 1;
          blockedUntil = Date.now() + cooldownMs();
          throw err instanceof HttpError ? err : new HttpError(401, err.message);
        }
      }
    }

    const joined = panelErrors.join(' · ');
    // قفل الحساب يُقال بكلمات أخرى، والخلط بينه وبين خطأ البيانات يضيّع الوقت
    const locked = /(kilit|çok fazla|cok fazla|deneme|bloke|askıya|askiya)/i.test(joined);

    const verdict = joined
      ? `رسالة اللوحة: «${joined}»${locked ? ' — الحساب مقفل مؤقتاً، لا علاقة للبيانات' : ''}`
      : gotCookies
        ? 'اللوحة أعادت صفحة الدخول بلا رسالة — البيانات مرفوضة على الأرجح'
        : 'اللوحة لم تمنح أي كوكي — قد تكون تحجب الطلبات الآلية';

    lastError =
      `فشل تسجيل الدخول — ${verdict} (المستخدم: ${username} [${valueShape(username)}] · ` +
      `كلمة السر: ${password.length} حرفاً [${valueShape(password)}] · ` +
      `الصفحة: ${result.url})`;

    failures += 1;
    blockedUntil = Date.now() + cooldownMs();
    log.warn(
      `eganis(http): محاولة فاشلة رقم ${failures} — أتوقّف ${cooldownMs() / 1000} ثانية حمايةً للحساب`,
    );

    throw new HttpError(401, lastError);
  }

  /**
   * الدخول عبر متصفّح حقيقي — مصافحة واحدة لا أكثر.
   *
   * حين تُشفّر اللوحة كلمة السر بجافاسكربت قبل إرسالها، لا يمكن لأي إرسال
   * خام أن ينجح مهما كانت البيانات صحيحة. فندع المتصفّح يفعل ما يفعله
   * صاحب الحساب: يفتح الصفحة، يكتب، يضغط. ثم نأخذ الكوكيز ونغلقه.
   *
   * ولأن القراءة بعدها تجري بـ HTTP، لا يبقى متصفّح مفتوحاً: ثوانٍ معدودة
   * مرة كل جلسة، لا مئات الميجابايتات دائمة.
   */
  async function loginViaBrowser(form) {
    const { username, password } = config.eganis;
    const { findChrome } = await import('../../lib/chrome.js');

    let playwright = null;
    for (const pkg of ['playwright', 'playwright-core']) {
      try {
        playwright = await import(pkg);
        break;
      } catch {
        /* نجرّب التالي */
      }
    }
    if (!playwright) throw new HttpError(500, 'حزمة playwright غير مثبّتة');

    const executablePath = findChrome();
    if (!executablePath) throw new HttpError(500, 'لا يوجد متصفّح على الخادم');

    log.info('eganis(http): الدخول عبر المتصفّح (مصافحة واحدة)');
    const browser = await playwright.chromium.launch({
      executablePath,
      args: [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-extensions',
        '--blink-settings=imagesEnabled=false',
        '--js-flags=--max-old-space-size=192',
        '--mute-audio',
        '--no-first-run',
      ],
    });

    try {
      const context = await browser.newContext({ locale: 'tr-TR', userAgent: UA });
      const page = await context.newPage();
      await page.goto(base(), { waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.waitForTimeout(1500);

      // نستخدم أسماء الحقول التي قرأناها من النموذج — أدقّ من التخمين
      const userSel = form?.userName ? `[name="${form.userName}"]` : 'input[type="text"], input[type="email"]';
      const passSel = form?.passwordName ? `[name="${form.passwordName}"]` : 'input[type="password"]';

      await page.locator(passSel).first().waitFor({ timeout: 20000 });
      await page.locator(userSel).first().fill(username);
      await page.locator(passSel).first().fill(password);

      // نقرأ ما استقرّ في الخانتين قبل الإرسال — بعده تُفرَّغ مع إعادة التحميل
      const typed = {
        user: await page.locator(userSel).first().inputValue().catch(() => ''),
        passwordLength: (await page.locator(passSel).first().inputValue().catch(() => '')).length,
      };

      await Promise.all([
        page.waitForLoadState('networkidle', { timeout: 30000 }).catch(() => {}),
        page
          .locator('form:has(input[type="password"]) button[type="submit"], form:has(input[type="password"]) input[type="submit"]')
          .first()
          .click({ timeout: 15000 })
          .catch(() => page.locator(passSel).first().press('Enter').catch(() => {})),
      ]);
      await page.waitForTimeout(2000);

      const stillLogin = await page.locator('input[type="password"]').filter({ visible: true }).count();
      if (stillLogin > 0) {
        /*
         * لقطة من داخل المحاولة نفسها — لا محاولة إضافية.
         * حين يُرفض متصفّح حقيقي بنفس البيانات، لم يبقَ ما يُشرح بالكلام:
         * يرى صاحب الحساب بعينه ما كُتب في الخانة وما ردّت به اللوحة.
         */
        lastLoginShot = {
          at: Date.now(),
          url: page.url(),
          typedUser: typed.user,
          typedPasswordLength: typed.passwordLength,
          image: await page.screenshot({ fullPage: true, type: 'png' }).catch(() => null),
        };

        const message = await page
          .evaluate(() => {
            const nodes = document.querySelectorAll(
              '.validation-summary-errors, .field-validation-error, .alert-danger, .text-danger, [role="alert"]',
            );
            return [...nodes].map((n) => (n.textContent || '').replace(/\s+/g, ' ').trim())
              .filter(Boolean).join(' · ').slice(0, 200);
          })
          .catch(() => '');
        throw new HttpError(
          401,
          `فشل الدخول عبر المتصفّح أيضاً${message ? ` — «${message}»` : ''} — البيانات مرفوضة من اللوحة`,
        );
      }

      // الكوكيز هي كل ما نحتاجه؛ القراءة بعدها بـ HTTP
      jar.clear();
      for (const cookie of await context.cookies()) jar.map.set(cookie.name, cookie.value);

      loggedIn = true;
      failures = 0;
      blockedUntil = 0;
      lastError = null;
      browserTried = false; // الجلسة القادمة تستحقّ محاولة جديدة
      preferBrowserLogin = true; // ولا نعيد عليها الإرسال الخام الفاشل
      log.info(`eganis(http): تم الدخول عبر المتصفّح (${jar.size} كوكي)`);
      return { url: base(), status: 200, html: '', trail: ['browser-login'] };
    } finally {
      await browser.close().catch(() => {});
    }
  }

  /** جلب صفحة داخل اللوحة، مع إعادة الدخول إن انتهت الجلسة */
  async function fetchPage(url) {
    if (!loggedIn) await login();
    let page = await request(url, { referer: base() });

    if (looksLikeLogin(page.html)) {
      loggedIn = false;
      await login();
      page = await request(url, { referer: base() });
      if (looksLikeLogin(page.html)) {
        throw new HttpError(401, `الجلسة لا تثبت — اللوحة تعيدنا لصفحة الدخول عند فتح ${short(url)}`);
      }
    }
    return page;
  }

  // ===== اكتشاف الصفحات =====

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

  async function panelLinks() {
    if (!loggedIn) await login();
    const home = await fetchPage(base());
    const links = extractLinks(home.html);
    const seen = new Set();
    return links.filter((l) => !seen.has(l.href) && seen.add(l.href));
  }

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

  async function discoverPages() {
    if (discovered) return discovered;

    const chosen = manualPages();
    if (chosen) {
      discovered = chosen;
      return discovered;
    }

    if (fs.existsSync(PAGES_CACHE)) {
      try {
        discovered = JSON.parse(fs.readFileSync(PAGES_CACHE, 'utf8'));
        if (Object.keys(discovered).length) return discovered;
      } catch {
        /* ملف تالف — نكتشف من جديد */
      }
    }

    const { found } = await autodetect({});
    discovered = found;
    return discovered;
  }

  /**
   * اكتشاف الصفحات بفحص محتواها لا بأسمائها: أسماء القوائم تختلف بين
   * تركيبات eganis، لكن أعمدة الجداول ثابتة.
   */
  async function autodetect({ limit = 16, onProgress } = {}) {
    const links = await panelLinks();
    const origin = base();

    const candidates = links
      .filter((link) => {
        const hay = normalizeHeader(`${link.text} ${link.href}`);
        if (!hay) return false;
        if (SKIP_WORDS.some((word) => hay.includes(word))) return false;
        if (/^https?:\/\//i.test(link.href) && !link.href.startsWith(origin)) return false;
        return true;
      })
      .slice(0, limit);

    const kinds = Object.entries(MAP_KIND);
    const examined = [];

    for (const [index, link] of candidates.entries()) {
      onProgress?.({ index: index + 1, total: candidates.length, text: link.text || link.href });
      try {
        const page = await fetchPage(resolve(link.href));
        for (const table of extractTables(page.html)) {
          if (!table.rows.length) continue;
          const scores = {};
          for (const [kind, mapKind] of kinds) scores[kind] = mappingScore(table.headers, mapKind);
          examined.push({ link, rows: table.rows.length, scores });
        }
      } catch (err) {
        log.debug(`eganis(http): تعذّر فحص ${link.href} — ${err.message}`);
      }
    }

    /*
     * كل صفحة شيء واحد: نحسب النوع الأعلى تطابقاً لكل جدول أولاً، ثم نوزّع
     * الأنواع. بلا هذا تبتلع صفحة العقود أنواعاً أخرى لأن جدولها يحوي
     * «Plaka» و«Müşteri» أيضاً.
     */
    const primary = examined.map((entry) => {
      const ranked = Object.entries(entry.scores)
        .map(([kind, s]) => ({ kind, ...s }))
        .sort((a, b) => b.score - a.score || b.matched - a.matched);
      return { ...entry, best: ranked[0], ranked };
    });

    const found = {};
    const taken = new Set();

    for (const kind of Object.keys(MAP_KIND)) {
      const owners = primary
        .filter((e) => e.best?.kind === kind && e.best.score > 0 && !taken.has(e.link.href))
        .sort((a, b) => b.best.score - a.best.score || b.rows - a.rows);

      const pick =
        owners[0] ||
        primary
          .filter((e) => !taken.has(e.link.href) && (e.scores[kind]?.score || 0) >= 0.5)
          .sort((a, b) => (b.scores[kind].score || 0) - (a.scores[kind].score || 0))[0];

      if (!pick) continue;
      taken.add(pick.link.href);
      found[kind] = {
        href: pick.link.href,
        text: pick.link.text,
        score: Number((pick.scores[kind]?.score || 0).toFixed(2)),
        rows: pick.rows,
      };
    }

    // احتياط: تسمية بالكلمات حين لا يكفي المحتوى
    for (const link of candidates) {
      const kind = classifyLink(link.text, link.href);
      if (kind && !found[kind] && !taken.has(link.href)) {
        found[kind] = { href: link.href, text: link.text, score: 0, byName: true };
        taken.add(link.href);
      }
    }

    try {
      fs.mkdirSync(path.dirname(PAGES_CACHE), { recursive: true });
      fs.writeFileSync(PAGES_CACHE, JSON.stringify(found, null, 2));
    } catch {
      /* لا قرص دائم — نكتفي بالذاكرة */
    }

    discovered = found;
    return { found, scanned: candidates.length };
  }

  /** قراءة صفحة وتحويل أنسب جدول فيها إلى سجلات التطبيق */
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

    const page = await fetchPage(resolve(target.href));
    const tables = extractTables(page.html).filter((t) => t.rows.length);
    if (!tables.length) {
      throw new HttpError(
        502,
        `صفحة "${kind}" بلا جدول قابل للقراءة — قد تُبنى بجافاسكربت (${short(page.url)})`,
      );
    }

    const mapKind = MAP_KIND[kind];
    const best = tables
      .map((t) => ({ t, score: mappingScore(t.headers, mapKind).score }))
      .sort((a, b) => b.score - a.score)[0];

    const rows = mapRows(best.t.headers, best.t.rows, mapKind);
    cache.set(kind, { at: Date.now(), rows });
    return rows;
  }

  const filterRows = (rows, filter) => {
    if (!filter || !Object.keys(filter).length) return rows;
    return rows.filter((row) =>
      Object.entries(filter).every(([key, value]) => {
        if (value === undefined || value === null || value === '') return true;
        return String(row[key] ?? '').toLowerCase() === String(value).toLowerCase();
      }),
    );
  };

  const notSupported = (what) => {
    throw new HttpError(501, `${what} غير مدعوم في وضع القراءة — نفّذه في لوحة eganis نفسها`);
  };

  return {
    name: 'eganis:http',

    async health() {
      try {
        const pages = await discoverPages();
        const found = Object.keys(pages);
        return {
          ok: true,
          driver: 'http',
          baseUrl: base(),
          pages: found,
          note: found.length ? undefined : 'لم أتعرّف على صفحات اللوحة — اخترها من شاشة الإعدادات',
        };
      } catch (err) {
        return { ok: false, driver: 'http', error: err.message };
      }
    },

    /** تشخيص الدخول بالنص: ماذا يطلب نموذج اللوحة، وهل نجح الدخول */
    async loginDiagnose() {
      const started = Date.now();
      const { username, password } = config.eganis;
      try {
        const page = await login();
        return {
          ok: true,
          url: base(),
          user: username,
          passwordLength: password.length,
          title: textOf((page.html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || ''),
          tookMs: Date.now() - started,
        };
      } catch (err) {
        let form = null;
        let title = '';
        let scripts = null;
        try {
          const landing = await request(base());
          form = findLoginForm(landing.html);
          scripts = analyzeLoginScripts(landing.html, form);
          title = textOf((landing.html.match(/<title\b[^>]*>([\s\S]*?)<\/title>/i) || [])[1] || '');
        } catch {
          /* نكتفي بما جمعناه */
        }
        /*
         * أحرف عربية في كلمة سر لاتينية = لوحة المفاتيح كانت عربية وقت
         * كتابتها. الخانة تُظهر نقاطاً فلا شيء ينبّه صاحبها. نعرض النسخة
         * المصحّحة ليتعرّف عليها بنفسه — ولا نستبدلها من تلقائنا.
         */
        const pw = describeValue(password);
        const user = describeValue(username);
        const fix = pw.arabicKeyboard
          ? {
              field: 'كلمة السر',
              reason: 'مكتوبة بأحرف عربية — كانت لوحة المفاتيح عربية وقت كتابتها',
              suggestion: arabicKeyboardToLatin(password),
            }
          : user.arabicKeyboard
            ? {
                field: 'اسم المستخدم',
                reason: 'مكتوب بأحرف عربية — كانت لوحة المفاتيح عربية وقت كتابته',
                suggestion: arabicKeyboardToLatin(username),
              }
            : null;

        return {
          ok: false,
          error: err.message,
          url: base(),
          user: username,
          userShape: user.text,
          passwordLength: password.length,
          passwordShape: pw.text,
          fix,
          title,
          form,
          summary: formSummary(form),
          // ما كُتب فعلاً في الخانتين داخل المتصفّح — يقطع الشكّ بأن التطبيق
          // يرسل شيئاً غير الذي حُفظ
          typed: lastLoginShot && {
            user: lastLoginShot.typedUser,
            passwordLength: lastLoginShot.typedPasswordLength,
          },
          shot: Boolean(lastLoginShot?.image),
          scripts: scripts && {
            جافاسكربت_يمسّ_كلمة_السر: scripts.touchesPassword,
            معالج_إرسال: scripts.submitHandler,
            إشارات_تشفير: scripts.cryptoHints,
            كابتشا: scripts.captcha,
            سكربتات_خارجية: scripts.externalScripts,
          },
          tookMs: Date.now() - started,
        };
      }
    },

    /**
     * ما رآه الخادم لحظة رفض اللوحة — لقطة من داخل المحاولة الأخيرة نفسها،
     * فعرضها لا يكلّف محاولة دخول جديدة ولا يقرّب الحساب من القفل.
     */
    async screenshot() {
      if (!lastLoginShot?.image) {
        throw new HttpError(
          501,
          'لا توجد لقطة بعد. اضغط «لماذا فشل الدخول؟» أولاً، فتُلتقط أثناء المحاولة.',
        );
      }
      return {
        url: lastLoginShot.url,
        title: 'آخر محاولة دخول',
        loggedIn: false,
        image: lastLoginShot.image,
      };
    },

    async links() {
      return panelLinks();
    },

    autodetect,

    async refresh() {
      cache.clear();
      discovered = null;
      loggedIn = false;
      jar.clear();
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
            id: `ret-${c.no}`, type: 'pickup', at: c.endAt, ref: c.no,
            plate: c.plate, driver: null, status: 'pending',
          });
        }
      }
      for (const b of bookings) {
        if (b.pickupAt && b.status !== 'cancelled') {
          tasks.push({
            id: `del-${b.no}`, type: 'delivery', at: b.pickupAt, ref: b.no,
            plate: b.plate || null, driver: null, status: 'pending',
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
      const source = rows.length
        ? rows
        : Object.values(
            (await readPage('contracts')).reduce((acc, c) => {
              const key = c.customerName || c.phone;
              if (key && !acc[key]) acc[key] = { id: key, name: c.customerName, phone: c.phone || null };
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

    async listLedgerEntries(customerId) {
      const rows = await readPage('ledger').catch(() => []);
      if (!rows.length) return [];
      const needle = String(customerId || '').toLowerCase();
      return rows
        .filter((r) => !needle || JSON.stringify(r).toLowerCase().includes(needle))
        .map((r) => ({ ...r, type: r.direction === 'credit' ? 'payment' : 'extra' }));
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
      jar.clear();
      loggedIn = false;
    },
  };
}
