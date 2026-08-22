/**
 * الربط الذكي: فهم جداول لوحة eganis بلا إعداد يدوي.
 *
 * لوحات eganis تركية، وأسماء أعمدتها ثابتة إلى حد بعيد. هنا نترجم:
 *   - أسماء الأعمدة  → حقول التطبيق  (Sözleşme No → no)
 *   - الأرقام التركية → أرقام         (3.000,50 → 3000.5)
 *   - التواريخ         → ISO          (18.08.2026 14:30 → 2026-08-18T14:30:00)
 *   - حالات العقود والمركبات → حالاتنا (Açık → open · Kirada → rented)
 *
 * كل دالة هنا خالصة (بلا شبكة ولا متصفّح) لتُختبر وحدها.
 */

/** مرادفات كل حقل: تركي (بحروف مبسّطة) وإنجليزي */
const FIELD_WORDS = {
  contract: {
    no: ['sozlesme no', 'sozlesmeno', 'sozlesme', 'kontrat no', 'contract no', 'contract'],
    customerName: ['musteri adi', 'musteri', 'ad soyad', 'customer', 'client', 'kiraci'],
    phone: ['telefon', 'gsm', 'cep', 'phone', 'mobile'],
    plate: ['plaka', 'plate', 'arac plaka'],
    startAt: ['baslangic', 'cikis tarihi', 'alis tarihi', 'start', 'baslama'],
    endAt: ['bitis', 'donus tarihi', 'iade tarihi', 'end', 'return'],
    status: ['durum', 'status', 'durumu'],
    dailyRate: ['gunluk', 'gunluk fiyat', 'birim fiyat', 'daily'],
    days: ['gun', 'gun sayisi', 'sure', 'days'],
    total: ['toplam', 'tutar', 'total', 'genel toplam'],
    paid: ['odenen', 'tahsil', 'tahsilat', 'paid'],
    balance: ['bakiye', 'kalan', 'balance', 'borc'],
    deposit: ['depozito', 'teminat', 'deposit'],
    currency: ['para birimi', 'doviz', 'currency', 'birim'],
    branch: ['sube', 'branch', 'ofis'],
  },
  vehicle: {
    plate: ['plaka', 'plate'],
    make: ['marka', 'make', 'brand'],
    model: ['model'],
    year: ['yil', 'model yili', 'year'],
    group: ['grup', 'sinif', 'segment', 'group', 'class'],
    status: ['durum', 'status'],
    branch: ['sube', 'branch', 'lokasyon', 'location'],
    odometer: ['km', 'kilometre', 'odometer'],
  },
  booking: {
    no: ['rezervasyon no', 'rez no', 'rez. no', 'reservation', 'booking'],
    customerName: ['musteri', 'ad soyad', 'customer'],
    phone: ['telefon', 'gsm', 'phone'],
    group: ['grup', 'sinif', 'group'],
    pickupAt: ['alis', 'cikis', 'pickup', 'teslim'],
    dropoffAt: ['donus', 'iade', 'dropoff', 'return'],
    branch: ['sube', 'branch'],
    status: ['durum', 'status'],
  },
  customer: {
    id: ['musteri no', 'cari kod', 'kod', 'customer no', 'id'],
    name: ['ad soyad', 'musteri adi', 'musteri', 'unvan', 'name', 'customer'],
    phone: ['telefon', 'gsm', 'cep', 'phone'],
    idNumber: ['tc kimlik', 'tc', 'kimlik', 'vergi no', 'passport', 'pasaport'],
    license: ['ehliyet', 'license'],
  },
  ledgerEntry: {
    occurredAt: ['tarih', 'date', 'islem tarihi'],
    note: ['aciklama', 'islem', 'description', 'detay'],
    ref: ['belge no', 'evrak no', 'sozlesme no', 'fis no', 'reference'],
    debit: ['borc', 'debit'],
    credit: ['alacak', 'credit'],
    balance: ['bakiye', 'balance'],
    amount: ['tutar', 'amount'],
    currency: ['para birimi', 'doviz', 'currency'],
  },
};

/** تبسيط النص: حروف تركية → لاتينية، بلا رموز، حروف صغيرة */
export function normalizeHeader(text) {
  return String(text || '')
    .toLocaleLowerCase('tr-TR')
    .replace(/ı/g, 'i')
    .replace(/İ/g, 'i')
    .replace(/ş/g, 's')
    .replace(/ğ/g, 'g')
    .replace(/ü/g, 'u')
    .replace(/ö/g, 'o')
    .replace(/ç/g, 'c')
    .replace(/[^\w\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * مطابقة أعمدة جدول بحقول التطبيق.
 * @returns {Record<string, number>} اسم الحقل → رقم العمود
 */
export function mapColumns(headers, kind) {
  const dictionary = FIELD_WORDS[kind];
  if (!dictionary) throw new Error(`نوع غير معروف: ${kind}`);

  const clean = headers.map(normalizeHeader);
  const mapping = {};
  const taken = new Set();

  // الأدق أولاً: تطابق كامل، ثم بداية العمود، ثم احتواء
  const strategies = [
    (col, word) => col === word,
    (col, word) => col.startsWith(`${word} `) || col.endsWith(` ${word}`),
    (col, word) => col.includes(word),
  ];

  for (const strategy of strategies) {
    for (const [field, words] of Object.entries(dictionary)) {
      if (mapping[field] !== undefined) continue;
      for (const word of words) {
        const index = clean.findIndex((col, i) => !taken.has(i) && col && strategy(col, word));
        if (index !== -1) {
          mapping[field] = index;
          taken.add(index);
          break;
        }
      }
    }
  }
  return mapping;
}

/** رقم بالصيغة التركية (1.234,56) أو الإنجليزية (1,234.56) */
export function parseNumber(value) {
  if (typeof value === 'number') return value;
  const text = String(value ?? '').replace(/[^\d.,-]/g, '');
  if (!text) return null;
  const lastComma = text.lastIndexOf(',');
  const lastDot = text.lastIndexOf('.');
  let normalized;
  if (lastComma === -1 && lastDot === -1) normalized = text;
  else if (lastComma > lastDot) normalized = text.replace(/\./g, '').replace(',', '.');
  else normalized = text.replace(/,/g, '');
  const number = Number(normalized);
  return Number.isFinite(number) ? number : null;
}

const pad = (n) => String(n).padStart(2, '0');

/**
 * تاريخ تركي (18.08.2026 أو 18/08/2026 14:30) → نص زمني محلي.
 *
 * نُعيده بلا لاحقة Z عمداً: «18.08.2026» في اللوحة تعني الثامن عشر بتوقيت
 * إسطنبول، ولو حوّلناه إلى UTC لصار 17 مساءً وانزاح يوم التسليم والإرجاع.
 */
export function parseDate(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;

  const m = /^(\d{1,2})[./-](\d{1,2})[./-](\d{4})(?:[\s,]+(\d{1,2}):(\d{2}))?/.exec(text);
  if (m) {
    const [, day, month, year, hour = '0', minute = '0'] = m;
    const d = Number(day);
    const mo = Number(month);
    if (d < 1 || d > 31 || mo < 1 || mo > 12) return null;
    return `${year}-${pad(mo)}-${pad(d)}T${pad(Number(hour))}:${pad(Number(minute))}:00`;
  }

  const parsed = new Date(text);
  if (Number.isNaN(parsed.getTime())) return null;
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}T${pad(
    parsed.getHours(),
  )}:${pad(parsed.getMinutes())}:00`;
}

const CONTRACT_STATUS = {
  acik: 'open',
  aktif: 'open',
  devam: 'open',
  kapali: 'closed',
  kapandi: 'closed',
  tamamlandi: 'closed',
  iade: 'closed',
  gecikmis: 'overdue',
  geciken: 'overdue',
  gecikme: 'overdue',
  iptal: 'cancelled',
};

const VEHICLE_STATUS = {
  musait: 'available',
  bos: 'available',
  hazir: 'available',
  kirada: 'rented',
  kiralik: 'rented',
  dolu: 'rented',
  bakim: 'maintenance',
  serviste: 'maintenance',
  servis: 'maintenance',
  hasarli: 'out_of_service',
  satildi: 'out_of_service',
};

const BOOKING_STATUS = {
  onayli: 'confirmed',
  onaylandi: 'confirmed',
  yeni: 'new',
  bekliyor: 'new',
  beklemede: 'new',
  iptal: 'cancelled',
};

function translateStatus(value, table) {
  const clean = normalizeHeader(value);
  if (!clean) return null;
  for (const [turkish, ours] of Object.entries(table)) {
    if (clean.includes(turkish)) return ours;
  }
  return clean; // نُبقي الأصل بدل أن نخترع حالة
}

export const contractStatus = (v) => translateStatus(v, CONTRACT_STATUS);
export const vehicleStatus = (v) => translateStatus(v, VEHICLE_STATUS);
export const bookingStatus = (v) => translateStatus(v, BOOKING_STATUS);

/** TL / ₺ / USD / $ → رمز العملة عندنا */
export function parseCurrency(value) {
  const text = String(value ?? '').toUpperCase();
  if (/USD|\$|DOLAR|DOLLAR/.test(text)) return 'USD';
  if (/TL|TRY|₺|LIRA/.test(text)) return 'TRY';
  return null;
}

const NUMERIC = new Set(['dailyRate', 'days', 'total', 'paid', 'balance', 'deposit', 'odometer', 'year', 'debit', 'credit', 'amount']);
const DATES = new Set(['startAt', 'endAt', 'pickupAt', 'dropoffAt', 'occurredAt', 'at']);

/**
 * تحويل صفوف جدول (مصفوفة نصوص) إلى سجلات التطبيق.
 * @param {string[]} headers ترويسة الجدول
 * @param {string[][]} rows الصفوف كنصوص
 * @param {string} kind contract | vehicle | booking | customer | ledgerEntry
 */
export function mapRows(headers, rows, kind) {
  const columns = mapColumns(headers, kind);
  const statusOf = { contract: contractStatus, vehicle: vehicleStatus, booking: bookingStatus }[kind];

  return rows.map((cells, rowIndex) => {
    const record = {};
    for (const [field, index] of Object.entries(columns)) {
      const raw = cells[index];
      if (raw === undefined || raw === null || raw === '') continue;

      if (NUMERIC.has(field)) record[field] = parseNumber(raw);
      else if (DATES.has(field)) record[field] = parseDate(raw);
      else if (field === 'currency') record[field] = parseCurrency(raw) || 'TRY';
      else if (field === 'status' && statusOf) record[field] = statusOf(raw);
      else record[field] = String(raw).trim();
    }

    // معرّف ثابت للسجل حتى لو لم توفّره اللوحة
    if (!record.id) record.id = record.no || record.plate || `row-${rowIndex + 1}`;
    if (kind === 'contract') {
      if (record.currency === undefined) record.currency = 'TRY';
      if (record.balance == null && record.total != null && record.paid != null) {
        record.balance = Math.round((record.total - record.paid) * 100) / 100;
      }
    }
    if (kind === 'ledgerEntry' && record.amount == null) {
      // بعض اللوحات تفصل مدين/دائن بدل عمود مبلغ واحد
      if (record.credit) {
        record.amount = record.credit;
        record.direction = 'credit';
      } else if (record.debit) {
        record.amount = record.debit;
        record.direction = 'debit';
      }
    }
    return record;
  });
}

/**
 * جودة المطابقة: كم حقلاً أساسياً وجدناه؟ تُستخدم لاختيار الجدول الصحيح
 * في صفحة فيها أكثر من جدول.
 */
export function mappingScore(headers, kind) {
  const columns = mapColumns(headers, kind);
  const essentials = {
    contract: ['no', 'customerName', 'startAt'],
    vehicle: ['plate', 'status'],
    booking: ['no', 'pickupAt'],
    customer: ['name'],
    ledgerEntry: ['occurredAt'],
  }[kind] || [];

  const found = essentials.filter((f) => columns[f] !== undefined).length;
  return { score: found / (essentials.length || 1), columns, matched: Object.keys(columns).length };
}

/**
 * تصنيف رابط في قائمة اللوحة إلى نوع صفحة.
 * الترتيب مقصود: الأكثر تحديداً أولاً، وتجنّبنا الكلمات القصيرة الملتبسة
 * (مثل "car" التي تقع داخل "cari hesap" وتعني الحساب لا المركبة).
 */
export const PAGE_HINTS = [
  { kind: 'ledger', words: ['cari', 'hesap', 'tahsilat', 'odeme', 'kasa', 'ekstre', 'account', 'payment'] },
  { kind: 'contracts', words: ['sozlesme', 'kiralama', 'kontrat', 'contract', 'rental'] },
  { kind: 'bookings', words: ['rezervasyon', 'reservation', 'booking'] },
  { kind: 'customers', words: ['musteri', 'customer', 'client', 'kiraci'] },
  { kind: 'vehicles', words: ['arac', 'vehicle', 'filo', 'fleet', 'plaka'] },
  { kind: 'documents', words: ['belge', 'dosya', 'evrak', 'document', 'foto', 'resim'] },
];

export function classifyLink({ text = '', href = '' }) {
  const haystack = `${normalizeHeader(text)} ${normalizeHeader(href)}`;
  for (const hint of PAGE_HINTS) {
    if (hint.words.some((word) => haystack.includes(word))) return hint.kind;
  }
  return null;
}
