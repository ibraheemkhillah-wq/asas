import fs from 'node:fs';
import path from 'node:path';

/** قراءة ملف .env بدون مكتبات خارجية */
function loadEnvFile(file) {
  if (!fs.existsSync(file)) return;
  const raw = fs.readFileSync(file, 'utf8');
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = value;
  }
}

loadEnvFile(path.resolve(process.cwd(), '.env'));

/** قيم البيئة تُنسخ يدوياً وقد تحمل فراغاً أو سطراً جديداً لا يُرى */
const str = (value, fallback = '') => (value === undefined ? fallback : String(value).trim());

/**
 * عنوان اللوحة كما ينسخه المستخدم من شريط المتصفّح يكون غالباً رابط صفحة
 * الدخول نفسها (…/Account/Login?ReturnUrl=…). لو أبقيناه كما هو صارت روابط
 * الصفحات الداخلية تُبنى فوقه فتخرج معطوبة، لذا نُرجعه إلى جذر اللوحة.
 */
const LOGIN_PATHS = /\/(account\/login|account\/signin|identity\/account\/login|login|signin|giris|uye\/giris|kullanici\/giris)\/?$/i;

export function panelBase(value) {
  const raw = str(value);
  if (!raw) return '';
  const withScheme = /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  try {
    const url = new URL(withScheme);
    url.search = '';
    url.hash = '';
    url.pathname = url.pathname.replace(LOGIN_PATHS, '') || '/';
    return url.toString().replace(/\/+$/, '');
  } catch {
    return raw.replace(/\/+$/, '');
  }
}

const bool = (v, fallback = false) => {
  if (v === undefined || v === '') return fallback;
  return ['1', 'true', 'yes', 'on'].includes(String(v).toLowerCase());
};

export const config = {
  port: Number(process.env.PORT || 3000),
  host: process.env.HOST || '0.0.0.0',
  timezone: process.env.TZ || 'Asia/Hebron',
  appToken: str(process.env.APP_TOKEN),
  dbPath: process.env.DB_PATH || './data/callrent.db',
  allowWrites: bool(process.env.ALLOW_WRITES, true),

  eganis: {
    driver: str(process.env.EGANIS_DRIVER, 'mock'),
    baseUrl: panelBase(process.env.EGANIS_BASE_URL),
    username: str(process.env.EGANIS_USERNAME),
    // كلمة السر تُقلَّم من الأطراف فقط — قد تحوي فراغاً في وسطها عمداً
    password: str(process.env.EGANIS_PASSWORD),
    apiKey: process.env.EGANIS_API_KEY || '',
    auth: process.env.EGANIS_AUTH || 'bearer',
    apiKeyHeader: process.env.EGANIS_API_KEY_HEADER || 'X-API-KEY',
    endpointsFile: process.env.EGANIS_ENDPOINTS_FILE || './config/eganis.json',
    // جلسة متصفّح محفوظة بتسجيل دخول يدوي (وضع browser)
    sessionFile: process.env.EGANIS_SESSION_FILE || './data/eganis-session.json',
    timeoutMs: Number(process.env.EGANIS_TIMEOUT_MS || 20000),
    // وضع المتصفّح: مدة الاحتفاظ بنتيجة الصفحة قبل إعادة قراءتها من eganis
    cacheSeconds: Number(process.env.EGANIS_CACHE_SECONDS || 20),
    // مهلة انتظار الجداول التي تُحمَّل بجافاسكربت
    pageWaitMs: Number(process.env.EGANIS_PAGE_WAIT_MS || 3000),
    // إغلاق المتصفّح بعد خمول بهذه الدقائق (0 = أبقِه مفتوحاً)
    idleCloseMinutes: Number(process.env.EGANIS_IDLE_CLOSE_MINUTES || 10),
    // صفحات اختارها المستخدم من شاشة الإعدادات: {"contracts":"/x","vehicles":"/y"}
    pages: process.env.EGANIS_PAGES || '',
  },

  whatsapp: {
    driver: process.env.WHATSAPP_DRIVER || 'mock',
    phoneNumberId: process.env.WA_PHONE_NUMBER_ID || '',
    token: process.env.WA_TOKEN || '',
    verifyToken: process.env.WA_VERIFY_TOKEN || 'callrent-verify',
    appSecret: process.env.WA_APP_SECRET || '',
    autoSend: bool(process.env.WA_AUTOSEND, false),
    graphVersion: process.env.WA_GRAPH_VERSION || 'v21.0',
  },

  fx: {
    // live = جلب السعر من المصادر · manual = اعتماد سعر الشركة الثابت
    mode: process.env.FX_MODE || 'live',
    // المصدر المفضّل: harem | tcmb | erapi | frankfurter | custom
    source: (process.env.FX_SOURCE || 'harem').toLowerCase(),
    manualRate: process.env.FX_USD_TRY || '',
    ttlMinutes: Number(process.env.FX_TTL_MINUTES || 15),
    autoRefresh: bool(process.env.FX_AUTO_REFRESH, true),
    // حرم ألتين — سعر السوق المعتمد في الصرافات
    haremUrl: process.env.FX_HAREM_URL || 'https://www.haremaltin.com/dovizapi/v1/doviz',
    haremField: (process.env.FX_HAREM_FIELD || 'satis').toLowerCase(), // satis | alis
    // آخر الحلول عند حجب حرم ألتين: متصفّح كامل. مطفأ افتراضياً لأن الخطط
    // الصغيرة (٥١٢ ميجا) تسقط تحته فيتعطّل التطبيق كلّه.
    haremViaBrowser: bool(process.env.FX_HAREM_VIA_BROWSER, false),
    // الصفحة التي نفتحها قبل الطلب، ليأتي من أصل الموقع نفسه بكوكيزه
    haremPageUrl: process.env.FX_HAREM_PAGE_URL || 'https://www.haremaltin.com/canli-piyasalar',
    // الحقل المعتمد من بيانات البنك المركزي التركي
    tcmbField: process.env.FX_TCMB_FIELD || 'ForexSelling',
    // مصدر تحدّده الشركة: أي رابط JSON ومسار الحقل داخله
    customUrl: process.env.FX_CUSTOM_URL || '',
    customPath: process.env.FX_CUSTOM_PATH || 'rate',
    customName: process.env.FX_CUSTOM_NAME || '',
  },

  ai: {
    apiKey: process.env.ANTHROPIC_API_KEY || '',
    model: process.env.ANTHROPIC_MODEL || 'claude-opus-5',
    companyProfileFile: process.env.COMPANY_PROFILE_FILE || './config/company.md',
  },
};

export function assertWritesAllowed() {
  if (!config.allowWrites) {
    const err = new Error('أوامر التعديل معطّلة (ALLOW_WRITES=false)');
    err.status = 403;
    throw err;
  }
}
