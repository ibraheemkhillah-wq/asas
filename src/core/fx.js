/**
 * أسعار الصرف — الليرة التركية / الدولار.
 *
 * الترتيب:
 *   1) سعر يدوي إن ضبطته الشركة (FX_MODE=manual أو من الواجهة) — كثير من المكاتب
 *      تعتمد سعرها الخاص في محاسبة العملاء.
 *   2) البنك المركزي التركي TCMB — المصدر الرسمي في تركيا (يُحدَّث أيام العمل).
 *   3) مصادر احتياطية مجانية عند تعذّر الأول.
 *   4) آخر سعر محفوظ (يُعلَّم بأنه قديم) حتى لا تتوقف الحسابات عند انقطاع الشبكة.
 *
 * كل سعر يُحفظ في قاعدة البيانات بوقته ومصدره، ويُعاد استخدامه ضمن مدة التخزين
 * المؤقت (FX_TTL_MINUTES) بدل استدعاء المصدر في كل طلب.
 */
import { get, run, all } from '../db.js';
import { config } from '../config.js';
import { fetchWithTimeout, HttpError } from '../lib/http.js';
import { log } from '../lib/log.js';
import { record } from './audit.js';

export const CURRENCIES = ['TRY', 'USD'];
export const SYMBOL = { TRY: '₺', USD: '$' };
export const CURRENCY_NAME = { TRY: 'الليرة التركية', USD: 'الدولار' };

const round2 = (n) => Math.round((Number(n) + Number.EPSILON) * 100) / 100;
const round4 = (n) => Math.round((Number(n) + Number.EPSILON) * 10000) / 10000;

export function isCurrency(value) {
  return normalizeCurrency(value, null) !== null;
}

/** أسماء العملة كما قد ترد من eganis أو من إدخال يدوي */
const ALIASES = {
  TRY: 'TRY', TL: 'TRY', TRL: 'TRY', '₺': 'TRY', LIRA: 'TRY', 'TÜRK LIRASI': 'TRY',
  'TURK LIRASI': 'TRY', 'ليرة': 'TRY', 'ل.ت': 'TRY',
  USD: 'USD', $: 'USD', US$: 'USD', DOLAR: 'USD', DOLLAR: 'USD', 'دولار': 'USD',
};

export function normalizeCurrency(value, fallback = 'TRY') {
  const key = String(value ?? '').trim().toUpperCase();
  return ALIASES[key] || fallback;
}

// ===== المصادر =====

/** البنك المركزي التركي — XML رسمي بلا مفتاح */
async function fromTcmb() {
  const res = await fetchWithTimeout('https://www.tcmb.gov.tr/kurlar/today.xml', {}, 12000);
  if (!res.ok) throw new Error(`TCMB ${res.status}`);
  const xml = await res.text();
  const block = /<Currency[^>]*CurrencyCode="USD"[\s\S]*?<\/Currency>/i.exec(xml);
  if (!block) throw new Error('لم يُعثر على الدولار في بيانات TCMB');
  const field = config.fx.tcmbField; // ForexSelling افتراضياً
  const value = new RegExp(`<${field}>([\\d.]+)</${field}>`, 'i').exec(block[0]);
  if (!value) throw new Error(`الحقل ${field} غير موجود في بيانات TCMB`);
  const rate = Number(value[1]);
  if (!Number.isFinite(rate) || rate <= 0) throw new Error('سعر TCMB غير صالح');
  return { rate, source: `TCMB (${field})` };
}

/** مصدر احتياطي مجاني */
async function fromErApi() {
  const res = await fetchWithTimeout('https://open.er-api.com/v6/latest/USD', {}, 12000);
  if (!res.ok) throw new Error(`er-api ${res.status}`);
  const json = await res.json();
  const rate = Number(json?.rates?.TRY);
  if (!Number.isFinite(rate) || rate <= 0) throw new Error('لا يوجد سعر TRY في الاستجابة');
  return { rate, source: 'open.er-api.com' };
}

/** مصدر احتياطي ثانٍ (أسعار البنك المركزي الأوروبي) */
async function fromFrankfurter() {
  const res = await fetchWithTimeout(
    'https://api.frankfurter.dev/v1/latest?base=USD&symbols=TRY',
    {},
    12000,
  );
  if (!res.ok) throw new Error(`frankfurter ${res.status}`);
  const json = await res.json();
  const rate = Number(json?.rates?.TRY);
  if (!Number.isFinite(rate) || rate <= 0) throw new Error('لا يوجد سعر TRY في الاستجابة');
  return { rate, source: 'frankfurter (ECB)' };
}

const PROVIDERS = [fromTcmb, fromErApi, fromFrankfurter];

// ===== التخزين =====

function lastStored() {
  return get('SELECT * FROM fx_rates ORDER BY id DESC LIMIT 1');
}

function store(rate, source) {
  run('INSERT INTO fx_rates (pair, rate, source) VALUES (?, ?, ?)', [
    'USD/TRY',
    round4(rate),
    source,
  ]);
  return lastStored();
}

const minutesSince = (iso) => (Date.now() - new Date(`${iso}Z`.replace('ZZ', 'Z')).getTime()) / 60000;

/**
 * سعر صرف الدولار مقابل الليرة الآن.
 * @param {{force?: boolean}} options force = تجاهل التخزين المؤقت
 * @returns {Promise<{rate:number, source:string, fetchedAt:string, stale:boolean, mode:string, ageMinutes:number}>}
 */
export async function getRate({ force = false } = {}) {
  // 1) سعر يدوي معتمد من الشركة
  if (config.fx.mode === 'manual') {
    const manual = Number(config.fx.manualRate);
    if (!Number.isFinite(manual) || manual <= 0) {
      throw new HttpError(500, 'FX_MODE=manual لكن FX_USD_TRY غير مضبوط');
    }
    return {
      rate: round4(manual),
      source: 'سعر الشركة (يدوي)',
      fetchedAt: new Date().toISOString(),
      stale: false,
      mode: 'manual',
      ageMinutes: 0,
    };
  }

  const cached = lastStored();
  const age = cached ? minutesSince(cached.created_at) : Infinity;
  if (!force && cached && age < config.fx.ttlMinutes) {
    return {
      rate: cached.rate,
      source: cached.source,
      fetchedAt: cached.created_at,
      stale: false,
      mode: 'live',
      ageMinutes: Math.round(age),
    };
  }

  const failures = [];
  for (const provider of PROVIDERS) {
    try {
      const { rate, source } = await provider();
      const saved = store(rate, source);
      log.info(`سعر الصرف: 1 دولار = ${rate} ليرة (${source})`);
      return {
        rate: saved.rate,
        source: saved.source,
        fetchedAt: saved.created_at,
        stale: false,
        mode: 'live',
        ageMinutes: 0,
      };
    } catch (err) {
      failures.push(`${provider.name}: ${err.message}`);
    }
  }

  log.warn(`تعذّر جلب سعر الصرف — ${failures.join(' | ')}`);

  if (cached) {
    return {
      rate: cached.rate,
      source: `${cached.source} (آخر سعر محفوظ)`,
      fetchedAt: cached.created_at,
      stale: true,
      mode: 'cached',
      ageMinutes: Math.round(age),
      error: failures.join(' | '),
    };
  }

  if (Number.isFinite(Number(config.fx.manualRate)) && Number(config.fx.manualRate) > 0) {
    return {
      rate: round4(config.fx.manualRate),
      source: 'السعر الاحتياطي من الإعدادات',
      fetchedAt: new Date().toISOString(),
      stale: true,
      mode: 'fallback',
      ageMinutes: 0,
    };
  }

  throw new HttpError(
    503,
    'تعذّر جلب سعر الصرف من كل المصادر، ولا يوجد سعر محفوظ. اضبط FX_USD_TRY في الإعدادات مؤقتاً.',
  );
}

/** ضبط سعر الشركة يدوياً (يُحفظ ويُستخدم كآخر سعر) */
export function setManualRate(rate, actor = 'dashboard') {
  const value = Number(rate);
  if (!Number.isFinite(value) || value <= 0) throw new HttpError(400, 'سعر صرف غير صالح');
  const saved = store(value, 'سعر أدخلته الشركة');
  record({ actor, action: 'fx_set_manual_rate', target: 'USD/TRY', payload: { rate: value } });
  return { rate: saved.rate, source: saved.source, fetchedAt: saved.created_at, mode: 'manual' };
}

export function rateHistory(limit = 30) {
  return all('SELECT * FROM fx_rates ORDER BY id DESC LIMIT ?', [limit]);
}

// ===== التحويل والعرض =====

/** تحويل مبلغ من عملة إلى أخرى بسعر محدّد */
export function convert(amount, from, to, rate) {
  const value = Number(amount) || 0;
  const source = normalizeCurrency(from);
  const target = normalizeCurrency(to);
  if (source === target) return round2(value);
  if (!Number.isFinite(rate) || rate <= 0) throw new HttpError(500, 'سعر الصرف غير صالح');
  return source === 'USD' ? round2(value * rate) : round2(value / rate);
}

/** صياغة مبلغ مع رمز عملته */
export function fmt(amount, currency) {
  const c = normalizeCurrency(currency);
  const value = Number(amount) || 0;
  const text = value.toLocaleString('ar-EG', { maximumFractionDigits: 2 });
  return c === 'USD' ? `${text} $` : `${text} ₺`;
}

/** «2,350 ₺ / 50 $» — العرض المزدوج الذي يعتمده أصحاب الشركة */
export function dual({ TRY: tryAmount = 0, USD: usdAmount = 0 }) {
  return `${fmt(tryAmount, 'TRY')} / ${fmt(usdAmount, 'USD')}`;
}
