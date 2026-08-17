/**
 * محاسبة المستأجرين — دفتر حساب لكل عميل.
 *
 * المبدأ: كل حركة مالية إمّا "لصالح العميل" (credit) أو "على العميل" (debit).
 *   credit : تأمين مستلم منه، دفعة نقدية، خصم                     → يزيد ما له عندنا
 *   debit  : أجرة عقد، تكاليف حادث، مخالفة، وقود، أو مبلغ أعدناه له → يقلّل ما له عندنا
 *
 * الرصيد النهائي = مجموع credit − مجموع debit
 *   موجب  → المبلغ مستحق للعميل (بدو منّا)
 *   سالب  → المبلغ مستحق علينا من العميل (بدنا منه)
 *   صفر   → الحساب مصفّى
 *
 * مصدر الحركات: eganis (عقود، تأمينات، دفعات) + حركات يدوية تُسجَّل هنا
 * (تكاليف حادث، إعادة تأمين، تصفية حساب…).
 */
import { all, get, run } from '../db.js';
import { eganis } from '../connectors/eganis/index.js';
import { HttpError } from '../lib/http.js';
import { assertWritesAllowed } from '../config.js';
import { record } from './audit.js';
import * as fx from './fx.js';

export const ENTRY_TYPES = {
  deposit: { label: 'تأمين مستلم', direction: 'credit' },
  payment: { label: 'دفعة من العميل', direction: 'credit' },
  discount: { label: 'خصم', direction: 'credit' },
  deposit_refund: { label: 'إعادة تأمين للعميل', direction: 'debit' },
  rent_charge: { label: 'أجرة عقد', direction: 'debit' },
  damage: { label: 'تكاليف حادث أو صيانة', direction: 'debit' },
  fine: { label: 'مخالفة مرورية', direction: 'debit' },
  fuel: { label: 'فرق وقود', direction: 'debit' },
  extra: { label: 'رسوم إضافية', direction: 'debit' },
  settlement: { label: 'تصفية حساب', direction: null },
};

const round2 = (n) => Math.round((Number(n) + Number.EPSILON) * 100) / 100;
const dateOnly = (value) => String(value || '').slice(0, 10);

function typeLabel(type) {
  return ENTRY_TYPES[type]?.label || type;
}

function directionFor(type, explicit) {
  if (explicit === 'credit' || explicit === 'debit') return explicit;
  const dir = ENTRY_TYPES[type]?.direction;
  if (!dir) {
    throw new HttpError(400, `نوع الحركة "${type}" يحتاج تحديد الاتجاه (credit أو debit)`);
  }
  return dir;
}

/** إيجاد العميل من eganis بالاسم أو الهاتف أو رقم الهوية أو المعرّف */
export async function findCustomer(query) {
  const q = String(query || '').trim();
  if (!q) throw new HttpError(400, 'أدخل اسم العميل أو رقم هاتفه');
  const driver = eganis();
  const results = await driver.searchCustomers(q);
  const list = Array.isArray(results) ? results : [];
  let match = list.find((c) => c.id === q || c.phone === q || c.idNumber === q) || list[0] || null;

  // بعض الموصلات لا تبحث بالمعرّف — نجرّب المطابقة على القائمة الكاملة
  if (!match) {
    const everyone = await driver.searchCustomers('');
    match =
      (everyone || []).find(
        (c) => c.id === q || c.phone === q || c.idNumber === q || String(c.name || '').includes(q),
      ) || null;
  }
  return { match, candidates: list.filter((c) => c.id !== match?.id) };
}

/**
 * حركات مأخوذة من eganis. إذا وفّر الموصل دالة listLedgerEntries استُخدمت،
 * وإلا اشتُقّت الحركات من العقود: تأمين + أجرة + المدفوع.
 */
async function eganisEntries(customer) {
  const driver = eganis();

  if (typeof driver.listLedgerEntries === 'function') {
    const rows = await driver.listLedgerEntries(customer.id);
    return (rows || []).map((r, i) => ({
      id: `eg-${r.id ?? i}`,
      type: r.type || 'extra',
      direction: directionFor(r.type || 'extra', r.direction),
      amount: round2(r.amount || 0),
      currency: fx.normalizeCurrency(r.currency),
      ref: r.ref || null,
      note: r.note || null,
      occurredAt: r.occurredAt || r.date || null,
      source: 'eganis',
    }));
  }

  const contracts = await driver.listContracts({ q: customer.phone || customer.name });
  const mine = (contracts || []).filter(
    (c) => c.customerId === customer.id || c.phone === customer.phone,
  );

  const entries = [];
  for (const c of mine) {
    // عملة العقد كما هي في eganis — لا تحويل عند التسجيل
    const currency = fx.normalizeCurrency(c.currency);
    if (Number(c.deposit) > 0) {
      entries.push({
        id: `eg-dep-${c.no}`,
        type: 'deposit',
        direction: 'credit',
        amount: round2(c.deposit),
        currency,
        ref: c.no,
        note: `تأمين عقد ${c.no} — مركبة ${c.plate}`,
        occurredAt: c.startAt,
        source: 'eganis',
      });
    }
    if (Number(c.total) > 0) {
      entries.push({
        id: `eg-rent-${c.no}`,
        type: 'rent_charge',
        direction: 'debit',
        amount: round2(c.total),
        currency,
        ref: c.no,
        note: `أجرة ${c.days} أيام × ${c.dailyRate}`,
        occurredAt: c.startAt,
        source: 'eganis',
      });
    }
    if (Number(c.paid) > 0) {
      entries.push({
        id: `eg-paid-${c.no}`,
        type: 'payment',
        direction: 'credit',
        amount: round2(c.paid),
        currency,
        ref: c.no,
        note: `دفعات على عقد ${c.no}`,
        occurredAt: c.startAt,
        source: 'eganis',
      });
    }
  }
  return entries;
}

/** الحركات اليدوية المسجّلة محلياً */
function manualEntries(customerId) {
  return all(
    `SELECT * FROM ledger_entries
     WHERE customer_id = ? AND voided = 0
     ORDER BY occurred_at, id`,
    [String(customerId)],
  ).map((r) => ({
    id: r.id,
    type: r.type,
    direction: r.direction,
    amount: round2(r.amount),
    currency: fx.normalizeCurrency(r.currency),
    ref: r.ref,
    note: r.note,
    occurredAt: r.occurred_at,
    source: r.source,
    author: r.author,
  }));
}

/**
 * كشف حساب كامل لعميل: الحركات مرتّبة زمنياً + الرصيد الجاري + الخلاصة.
 * @param {string} query اسم العميل أو هاتفه أو معرّفه
 */
export async function statement(query) {
  const { match: customer, candidates } = await findCustomer(query);
  if (!customer) {
    return { found: false, candidates: [], message: `لا يوجد عميل مطابق لـ "${query}"` };
  }

  const merged = [...(await eganisEntries(customer)), ...manualEntries(customer.id)].sort(
    (a, b) => String(a.occurredAt).localeCompare(String(b.occurredAt)) || String(a.id).localeCompare(String(b.id)),
  );

  // رصيد جارٍ منفصل لكل عملة — لا نخلط الليرة بالدولار في الحساب نفسه
  const running = { TRY: 0, USD: 0 };
  const entries = merged.map((e) => {
    const currency = fx.normalizeCurrency(e.currency);
    const credit = e.direction === 'credit' ? e.amount : 0;
    const debit = e.direction === 'debit' ? e.amount : 0;
    running[currency] = round2(running[currency] + credit - debit);
    return {
      ...e,
      currency,
      label: typeLabel(e.type),
      date: dateOnly(e.occurredAt),
      credit,
      debit,
      running: running[currency],
      runningAll: { ...running },
    };
  });

  const inCurrency = (currency, predicate = () => true) =>
    entries.filter((e) => e.currency === currency && predicate(e));

  const sumOf = (currency, predicate) =>
    round2(inCurrency(currency, predicate).reduce((total, e) => total + e.amount, 0));

  const byCurrency = {};
  for (const currency of fx.CURRENCIES) {
    const credits = round2(inCurrency(currency).reduce((t, e) => t + e.credit, 0));
    const debits = round2(inCurrency(currency).reduce((t, e) => t + e.debit, 0));
    const depositsIn = sumOf(currency, (e) => e.type === 'deposit');
    const depositsBack = sumOf(currency, (e) => e.type === 'deposit_refund');
    byCurrency[currency] = {
      credits,
      debits,
      net: round2(credits - debits),
      depositsIn,
      depositsBack,
      depositsHeld: round2(depositsIn - depositsBack),
      rentCharges: sumOf(currency, (e) => e.type === 'rent_charge'),
      damages: sumOf(currency, (e) => e.type === 'damage'),
      fines: sumOf(currency, (e) => e.type === 'fine'),
      payments: sumOf(currency, (e) => e.type === 'payment'),
      entries: inCurrency(currency).length,
    };
  }

  // سعر الصرف لحظة إعداد الكشف — للعرض المزدوج فقط، لا يغيّر الأرصدة الأصلية
  let rate = null;
  let rateError = null;
  try {
    rate = await fx.getRate();
  } catch (err) {
    rateError = err.message;
  }

  const netTry = byCurrency.TRY.net;
  const netUsd = byCurrency.USD.net;
  const combined = rate
    ? {
        inTRY: round2(netTry + fx.convert(netUsd, 'USD', 'TRY', rate.rate)),
        inUSD: round2(fx.convert(netTry, 'TRY', 'USD', rate.rate) + netUsd),
      }
    : null;

  // الحالة تُحسب على المكافئ الإجمالي، وإن تعذّر السعر فعلى العملتين معاً
  const combinedNet = combined ? combined.inTRY : netTry + netUsd;
  const status = combinedNet > 0.5 ? 'company_owes' : combinedNet < -0.5 ? 'customer_owes' : 'settled';

  // حالة واقعية: له رصيد بالدولار وعليه مستحقات بالليرة في آن واحد
  const mixed = (netTry > 0.005 && netUsd < -0.005) || (netTry < -0.005 && netUsd > 0.005);

  return {
    found: true,
    customer,
    candidates: candidates.filter((c) => c.id !== customer.id),
    entries,
    byCurrency,
    /** الأرصدة كما هي بعملتها الأصلية */
    net: { TRY: netTry, USD: netUsd },
    /** «2,350 ₺ / 50 $» */
    netText: fx.dual({ TRY: netTry, USD: netUsd }),
    fx: rate ? { ...rate, error: rateError } : { error: rateError },
    combined,
    status,
    /** true عندما يكون له رصيد بعملة وعليه مستحقات بالعملة الأخرى */
    mixed,
    /** ما نُعيده للعميل بكل عملة */
    toRefund: { TRY: netTry > 0 ? netTry : 0, USD: netUsd > 0 ? netUsd : 0 },
    /** ما نطالبه به بكل عملة */
    toCollect: { TRY: netTry < 0 ? round2(-netTry) : 0, USD: netUsd < 0 ? round2(-netUsd) : 0 },
    generatedAt: new Date().toISOString(),
  };
}

/**
 * نص كشف الحساب جاهزاً للإرسال للعميل (واتساب أو نسخ).
 * كل مبلغ يظهر بعملته الأصلية، والخلاصة تظهر بالليرة والدولار معاً
 * مع سعر الصرف المعتمد لحظة إعداد الكشف.
 */
export function statementText(stmt, { company = 'CALL & RENT' } = {}) {
  if (!stmt.found) return stmt.message;

  const lines = [];
  lines.push(`*${company} — كشف حساب*`);
  lines.push(`العميل: ${stmt.customer.name}`);
  lines.push(`التاريخ: ${dateOnly(stmt.generatedAt)}`);
  lines.push('');
  lines.push('*الحركات:*');
  for (const e of stmt.entries) {
    const sign = e.credit ? '+' : '−';
    const amount = fx.fmt(e.credit || e.debit, e.currency);
    const ref = e.ref ? ` (${e.ref})` : '';
    lines.push(`${e.date} · ${e.label}${ref}: ${sign}${amount}`);
  }
  lines.push('');

  // ملخّص لكل عملة استُخدمت فعلاً
  const used = fx.CURRENCIES.filter((c) => stmt.byCurrency[c].entries > 0);
  for (const c of used) {
    const b = stmt.byCurrency[c];
    lines.push(`*${fx.CURRENCY_NAME[c]}*`);
    lines.push(`  ما دفعته وتأميناتك: ${fx.fmt(b.credits, c)}`);
    lines.push(`  المستحقات عليك: ${fx.fmt(b.debits, c)}`);
    lines.push(`  الرصيد: ${fx.fmt(b.net, c)}`);
  }
  lines.push('');

  const dualNonZero = (amounts) =>
    fx.CURRENCIES.filter((c) => Math.abs(amounts[c]) > 0.005)
      .map((c) => fx.fmt(amounts[c], c))
      .join(' و ');

  if (stmt.mixed) {
    // رصيد بعملة ومستحقات بالعملة الأخرى — يُعرضان معاً بلا دمج
    lines.push(`*مستحق لك: ${dualNonZero(stmt.toRefund)}*`);
    lines.push(`*مستحق علينا منك: ${dualNonZero(stmt.toCollect)}*`);
  } else if (stmt.status === 'company_owes') {
    lines.push(`*الرصيد النهائي: ${dualNonZero(stmt.toRefund)} مستحقة لك ونحن جاهزون لإعادتها.*`);
  } else if (stmt.status === 'customer_owes') {
    lines.push(`*الرصيد النهائي: ${dualNonZero(stmt.toCollect)} مستحقة علينا منك.*`);
  } else {
    lines.push('*الرصيد النهائي: صفر — الحساب مصفّى بالكامل.*');
  }

  if (stmt.combined && stmt.fx?.rate) {
    const equivalent =
      stmt.status === 'customer_owes'
        ? { TRY: round2(-stmt.combined.inTRY), USD: round2(-stmt.combined.inUSD) }
        : { TRY: stmt.combined.inTRY, USD: stmt.combined.inUSD };
    const label = stmt.mixed ? 'صافي الفرق بعد التحويل' : 'المكافئ الإجمالي';
    lines.push(`${label}: ${fx.fmt(equivalent.TRY, 'TRY')} أو ${fx.fmt(equivalent.USD, 'USD')}`);
    lines.push(`سعر الصرف المعتمد: 1 $ = ${fx.fmt(stmt.fx.rate, 'TRY')} — ${stmt.fx.source}`);
  }
  return lines.join('\n');
}

/** إضافة حركة يدوية (تكاليف حادث، إعادة تأمين، دفعة نقدية…) */
export function addEntry(input, actor = 'dashboard') {
  assertWritesAllowed();
  const {
    customerId,
    customerName = null,
    phone = null,
    type,
    amount,
    currency = 'TRY',
    direction,
    ref = null,
    note = null,
    occurredAt,
  } = input;

  if (!customerId) throw new HttpError(400, 'معرّف العميل مطلوب');
  if (!ENTRY_TYPES[type]) {
    throw new HttpError(400, `نوع حركة غير معروف: ${type}. المسموح: ${Object.keys(ENTRY_TYPES).join(', ')}`);
  }
  const value = Number(amount);
  if (!Number.isFinite(value) || value <= 0) throw new HttpError(400, 'المبلغ يجب أن يكون رقماً أكبر من صفر');
  if (!fx.isCurrency(currency)) {
    throw new HttpError(400, `عملة غير مدعومة: ${currency}. المسموح: ${fx.CURRENCIES.join(' أو ')}`);
  }
  // الحركة تُسجَّل بعملتها كما حدثت — التحويل للعرض فقط
  const cur = fx.normalizeCurrency(currency);

  const dir = directionFor(type, direction);
  const when = occurredAt || new Date().toISOString();

  run(
    `INSERT INTO ledger_entries
       (customer_id, customer_name, phone, type, direction, amount, currency, ref, note, occurred_at, source, author)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual', ?)`,
    [String(customerId), customerName, phone, type, dir, round2(value), cur, ref, note, when, actor],
  );

  const created = get('SELECT * FROM ledger_entries WHERE id = last_insert_rowid()');
  record({
    actor,
    action: 'ledger_add_entry',
    target: String(customerId),
    payload: { type, amount: round2(value), currency: cur, direction: dir, ref },
    result: { id: created.id },
  });
  return created;
}

/** إلغاء حركة يدوية (لا تُحذف — تبقى في السجل للمراجعة) */
export function voidEntry(id, actor = 'dashboard') {
  assertWritesAllowed();
  const entry = get('SELECT * FROM ledger_entries WHERE id = ?', [id]);
  if (!entry) throw new HttpError(404, `لا توجد حركة بالرقم ${id}`);
  run('UPDATE ledger_entries SET voided = 1 WHERE id = ?', [id]);
  record({ actor, action: 'ledger_void_entry', target: String(entry.customer_id), payload: { id } });
  return { ok: true };
}

/**
 * تصفية حساب العميل: تُسجَّل حركة مقابلة لرصيد كل عملة فيصبح صفراً.
 * رصيد الليرة يُصفّى بحركة بالليرة، ورصيد الدولار بحركة بالدولار — لا خلط بينهما.
 *
 * @param {object} options
 *   currency : تصفية عملة واحدة فقط (TRY أو USD)، والافتراضي كل العملات
 *   payIn    : العملة التي استُلم/دُفع بها فعلياً — تُذكر في الملاحظة مع
 *              مكافئها بسعر اللحظة، مع بقاء الحركة بعملة الرصيد الأصلية
 */
export async function settle(
  query,
  { note = null, method = 'نقداً', currency = null, payIn = null } = {},
  actor = 'dashboard',
) {
  assertWritesAllowed();
  const stmt = await statement(query);
  if (!stmt.found) throw new HttpError(404, stmt.message);

  const only = currency ? fx.normalizeCurrency(currency, null) : null;
  if (currency && !only) throw new HttpError(400, `عملة غير مدعومة: ${currency}`);

  const targets = fx.CURRENCIES.filter(
    (c) => (!only || c === only) && Math.abs(stmt.net[c]) > 0.005,
  );
  if (!targets.length) {
    return { ok: true, alreadySettled: true, statement: stmt };
  }

  const cash = payIn ? fx.normalizeCurrency(payIn, null) : null;
  if (payIn && !cash) throw new HttpError(400, `عملة غير مدعومة: ${payIn}`);
  const settled = [];

  for (const c of targets) {
    const net = stmt.net[c];
    const owedToCustomer = net > 0;
    const amount = round2(Math.abs(net));
    const base = owedToCustomer
      ? `إعادة رصيد للعميل (${method})`
      : `تحصيل مستحقات من العميل (${method})`;

    // الدفع بعملة أخرى: الحركة تبقى بعملة الرصيد، والملاحظة توثّق المبلغ المستلم فعلاً
    let label = base;
    if (cash && cash !== c && stmt.fx?.rate) {
      label += ` — ${owedToCustomer ? 'سُلّم' : 'استُلم'} ${fx.fmt(
        fx.convert(amount, c, cash, stmt.fx.rate),
        cash,
      )} بسعر ${fx.fmt(stmt.fx.rate, 'TRY')} للدولار`;
    }

    addEntry(
      {
        customerId: stmt.customer.id,
        customerName: stmt.customer.name,
        phone: stmt.customer.phone,
        type: 'settlement',
        direction: owedToCustomer ? 'debit' : 'credit',
        amount,
        currency: c,
        note: note ? `${label} — ${note}` : label,
        occurredAt: new Date().toISOString(),
      },
      actor,
    );

    settled.push({ currency: c, amount, direction: owedToCustomer ? 'debit' : 'credit' });
  }

  record({
    actor,
    action: 'ledger_settle',
    target: stmt.customer.id,
    payload: { settled, method, payIn: cash },
  });

  const after = await statement(stmt.customer.id);
  const settledAmount = { TRY: 0, USD: 0 };
  for (const s of settled) settledAmount[s.currency] = s.amount;

  return {
    ok: true,
    settled,
    settledAmount,
    settledText: fx.dual(settledAmount),
    statement: after,
  };
}

/** قائمة العملاء الذين لهم أو عليهم رصيد — لمتابعة المطالبات والإرجاعات */
export async function openBalances() {
  const driver = eganis();
  const customers = await driver.searchCustomers('');
  const rows = [];
  for (const customer of customers || []) {
    const stmt = await statement(customer.id);
    if (!stmt.found || stmt.status === 'settled') continue;
    rows.push({
      customer: stmt.customer,
      net: stmt.net,
      netText: stmt.netText,
      combined: stmt.combined,
      status: stmt.status,
      mixed: stmt.mixed,
      toRefund: stmt.toRefund,
      toCollect: stmt.toCollect,
      depositsHeld: {
        TRY: stmt.byCurrency.TRY.depositsHeld,
        USD: stmt.byCurrency.USD.depositsHeld,
      },
    });
  }
  // الترتيب حسب حجم الرصيد بمكافئه بالليرة ليجتمع العملاء بالعملتين في قائمة واحدة
  const weight = (r) => Math.abs(r.combined ? r.combined.inTRY : r.net.TRY + r.net.USD);
  return rows.sort((a, b) => weight(b) - weight(a));
}
