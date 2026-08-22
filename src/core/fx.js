/**
 * أسعار الصرف — الليرة التركية / الدولار.
 *
 * الترتيب:
 *   1) سعر يدوي إن ضبطته الشركة (FX_MODE=manual أو من الواجهة).
 *   2) **حرم ألتين (haremaltin.com)** — سعر السوق المعتمد في الصرافات، وهو
 *      المصدر الافتراضي لأن الشركة تحاسب عملاءها عليه.
 *   3) البنك المركزي التركي TCMB ثم مصادر احتياطية عند تعذّر الأول.
 *   4) آخر سعر محفوظ (يُعلَّم بأنه قديم) حتى لا تتوقف الحسابات عند انقطاع الشبكة.
 *
 * كل سعر يُحفظ في قاعدة البيانات بوقته ومصدره، ويُعاد استخدامه ضمن مدة التخزين
 * المؤقت (FX_TTL_MINUTES) بدل استدعاء المصدر في كل طلب، ومهمة دورية تُحدّثه
 * تلقائياً في الخلفية فيكون جاهزاً قبل أن يُطلب.
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

/**
 * قراءة رقم قد يأتي بصيغة تركية («48,0500») أو إنجليزية («48.0500»)
 * أو بفواصل آلاف («1.234,56»). آخر فاصلة/نقطة هي الفاصلة العشرية.
 */
export function parseRateNumber(value) {
  if (typeof value === 'number') return Number.isFinite(value) ? value : NaN;
  const text = String(value ?? '').trim().replace(/[^\d.,-]/g, '');
  if (!text) return NaN;
  const lastComma = text.lastIndexOf(',');
  const lastDot = text.lastIndexOf('.');
  let normalized;
  if (lastComma === -1 && lastDot === -1) {
    normalized = text;
  } else if (lastComma > lastDot) {
    normalized = text.replace(/\./g, '').replace(',', '.');
  } else {
    normalized = text.replace(/,/g, '');
  }
  return Number(normalized);
}

/** التقاط سعر الدولار من أي شكل استجابة يعيده حرم ألتين */
export function pickHaremRate(json, field = 'satis') {
  const data = json?.data ?? json;
  const row =
    data?.USDTRY ??
    data?.USDTRY_?.[0] ??
    (data && typeof data === 'object'
      ? Object.entries(data).find(([key]) => /^USD ?\/? ?TRY$|^USDTRY$/i.test(key))?.[1]
      : null);
  if (!row) throw new Error('لم يُعثر على USDTRY في استجابة حرم ألتين');
  const raw = row[field] ?? row[field === 'satis' ? 'satış' : 'alış'] ?? row.satis ?? row.alis;
  const rate = parseRateNumber(raw);
  if (!Number.isFinite(rate) || rate <= 0) throw new Error(`قيمة ${field} غير صالحة: ${raw}`);
  return rate;
}

/**
 * حرم ألتين — سعر السوق الذي تعتمده الصرافات في إسطنبول.
 * `satis` = سعر البيع (الأعلى، وهو ما يظهر في تطبيق حرم)، و`alis` = الشراء.
 */
async function fromHarem() {
  const url = config.fx.haremUrl;
  const res = await fetchWithTimeout(
    url,
    {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        Accept: 'application/json, text/javascript, */*; q=0.01',
        Referer: 'https://www.haremaltin.com/canli-piyasalar',
        'User-Agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      },
      body: 'dil_kodu=tr',
    },
    12000,
  );
  if (!res.ok) throw new Error(`حرم ألتين ${res.status}`);
  const json = await res.json();
  const field = config.fx.haremField; // satis افتراضياً
  const rate = pickHaremRate(json, field);
  // تحقّق من المعقولية حتى لا يدخل رقم مشوّه إلى الحسابات
  if (rate < 1 || rate > 10000) throw new Error(`سعر غير معقول من حرم ألتين: ${rate}`);
  return { rate, source: `حرم ألتين (${field === 'alis' ? 'شراء' : 'بيع'})` };
}

/** مصدر تحدّده الشركة بنفسها: أي رابط JSON + مسار الحقل داخل الاستجابة */
async function fromCustom() {
  const url = config.fx.customUrl;
  if (!url) throw new Error('لا يوجد مصدر مخصّص');
  const res = await fetchWithTimeout(url, { headers: { Accept: 'application/json' } }, 12000);
  if (!res.ok) throw new Error(`المصدر المخصّص ${res.status}`);
  const json = await res.json();
  const value = config.fx.customPath
    .split('.')
    .reduce((node, key) => (node == null ? node : node[key]), json);
  const rate = parseRateNumber(value);
  if (!Number.isFinite(rate) || rate <= 0) {
    throw new Error(`لا يوجد سعر صالح في ${config.fx.customPath}`);
  }
  return { rate, source: config.fx.customName || 'مصدر الشركة المخصّص' };
}

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

const SOURCES = {
  harem: { fn: fromHarem, label: 'حرم ألتين (سعر السوق)' },
  custom: { fn: fromCustom, label: 'مصدر الشركة المخصّص' },
  tcmb: { fn: fromTcmb, label: 'البنك المركزي التركي' },
  erapi: { fn: fromErApi, label: 'open.er-api.com' },
  frankfurter: { fn: fromFrankfurter, label: 'frankfurter (ECB)' },
};

/** ترتيب المصادر: المفضّل أولاً ثم البقية كاحتياطي */
function providerOrder() {
  const preferred = String(config.fx.source || 'harem').toLowerCase();
  const keys = Object.keys(SOURCES);
  const ordered = [preferred, ...keys.filter((k) => k !== preferred)].filter((k) => SOURCES[k]);
  // المصدر المخصّص لا يُجرَّب إلا إذا ضبطته الشركة
  return ordered.filter((k) => k !== 'custom' || config.fx.customUrl);
}

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
  for (const key of providerOrder()) {
    try {
      const { rate, source } = await SOURCES[key].fn();
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
      failures.push(`${SOURCES[key].label}: ${err.message}`);
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

/**
 * فحص كل المصادر وإظهار ما أعادته كل واحدة — لتشخيص الربط على الخادم:
 * أي مصدر يعمل، وأيها محجوب، وكم يبعد سعره عن غيره.
 */
export async function checkSources() {
  const results = [];
  for (const key of Object.keys(SOURCES)) {
    if (key === 'custom' && !config.fx.customUrl) {
      results.push({ key, label: SOURCES[key].label, ok: false, skipped: true, error: 'غير مضبوط' });
      continue;
    }
    const startedAt = Date.now();
    try {
      const { rate, source } = await SOURCES[key].fn();
      results.push({ key, label: SOURCES[key].label, ok: true, rate, source, ms: Date.now() - startedAt });
    } catch (err) {
      results.push({
        key,
        label: SOURCES[key].label,
        ok: false,
        error: err.message,
        ms: Date.now() - startedAt,
      });
    }
  }
  const preferred = String(config.fx.source || 'harem').toLowerCase();
  return {
    preferred,
    order: providerOrder(),
    results,
    working: results.filter((r) => r.ok).map((r) => r.key),
    checkedAt: new Date().toISOString(),
  };
}

let refreshTimer = null;

/** تحديث تلقائي في الخلفية كل FX_TTL_MINUTES حتى يكون السعر جاهزاً دائماً */
export function startAutoRefresh() {
  if (refreshTimer || config.fx.mode === 'manual' || !config.fx.autoRefresh) return null;
  const everyMs = Math.max(1, config.fx.ttlMinutes) * 60000;

  const tick = async () => {
    try {
      const rate = await getRate({ force: true });
      log.info(`تحديث تلقائي لسعر الصرف: 1 $ = ${rate.rate} ₺ (${rate.source})`);
    } catch (err) {
      log.warn(`تعذّر التحديث التلقائي لسعر الصرف — ${err.message}`);
    }
  };

  refreshTimer = setInterval(tick, everyMs);
  refreshTimer.unref?.();
  tick(); // جلب أول سعر فور الإقلاع
  return refreshTimer;
}

export function stopAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = null;
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

/** صياغة مبلغ مع رمز عملته — الأرقام إنجليزية دائماً (1,234.56) */
export function fmt(amount, currency) {
  const c = normalizeCurrency(currency);
  const value = Number(amount) || 0;
  const text = value.toLocaleString('en-US', { maximumFractionDigits: 2 });
  return c === 'USD' ? `${text} $` : `${text} ₺`;
}

/** «2,350 ₺ / 50 $» — العرض المزدوج الذي يعتمده أصحاب الشركة */
export function dual({ TRY: tryAmount = 0, USD: usdAmount = 0 }) {
  return `${fmt(tryAmount, 'TRY')} / ${fmt(usdAmount, 'USD')}`;
}
