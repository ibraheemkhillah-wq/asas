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
    if (Number(c.deposit) > 0) {
      entries.push({
        id: `eg-dep-${c.no}`,
        type: 'deposit',
        direction: 'credit',
        amount: round2(c.deposit),
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

  let running = 0;
  const entries = merged.map((e) => {
    const credit = e.direction === 'credit' ? e.amount : 0;
    const debit = e.direction === 'debit' ? e.amount : 0;
    running = round2(running + credit - debit);
    return {
      ...e,
      label: typeLabel(e.type),
      date: dateOnly(e.occurredAt),
      credit,
      debit,
      running,
    };
  });

  const sum = (predicate) =>
    round2(entries.filter(predicate).reduce((total, e) => total + e.amount, 0));

  const credits = round2(entries.reduce((t, e) => t + e.credit, 0));
  const debits = round2(entries.reduce((t, e) => t + e.debit, 0));
  const net = round2(credits - debits);

  const depositsIn = sum((e) => e.type === 'deposit');
  const depositsBack = sum((e) => e.type === 'deposit_refund');

  return {
    found: true,
    customer,
    candidates: candidates.filter((c) => c.id !== customer.id),
    entries,
    totals: {
      credits,
      debits,
      net,
      depositsIn,
      depositsBack,
      depositsHeld: round2(depositsIn - depositsBack),
      rentCharges: sum((e) => e.type === 'rent_charge'),
      damages: sum((e) => e.type === 'damage'),
      fines: sum((e) => e.type === 'fine'),
      payments: sum((e) => e.type === 'payment'),
    },
    status: net > 0 ? 'company_owes' : net < 0 ? 'customer_owes' : 'settled',
    /** المبلغ الذي نُعيده للعميل (إن وُجد) */
    toRefund: net > 0 ? net : 0,
    /** المبلغ الذي نطالب به العميل (إن وُجد) */
    toCollect: net < 0 ? round2(-net) : 0,
    currency: '₺',
    generatedAt: new Date().toISOString(),
  };
}

/** نص كشف الحساب جاهزاً للإرسال للعميل (واتساب أو نسخ) */
export function statementText(stmt, { company = 'CALL & RENT' } = {}) {
  if (!stmt.found) return stmt.message;
  const c = stmt.currency;
  const lines = [];
  lines.push(`*${company} — كشف حساب*`);
  lines.push(`العميل: ${stmt.customer.name}`);
  lines.push(`التاريخ: ${dateOnly(stmt.generatedAt)}`);
  lines.push('');
  lines.push('*الحركات:*');
  for (const e of stmt.entries) {
    const amount = e.credit ? `+${e.credit}` : `-${e.debit}`;
    const ref = e.ref ? ` (${e.ref})` : '';
    lines.push(`${e.date} · ${e.label}${ref}: ${amount} ${c}`);
  }
  lines.push('');
  lines.push(`إجمالي ما دفعه/تأميناته: ${stmt.totals.credits} ${c}`);
  lines.push(`إجمالي المستحقات عليه: ${stmt.totals.debits} ${c}`);
  lines.push('');
  if (stmt.status === 'company_owes') {
    lines.push(`*الرصيد النهائي: ${stmt.toRefund} ${c} مستحقة لك ونحن جاهزون لإعادتها.*`);
  } else if (stmt.status === 'customer_owes') {
    lines.push(`*الرصيد النهائي: ${stmt.toCollect} ${c} مستحقة علينا منك.*`);
  } else {
    lines.push('*الرصيد النهائي: صفر — الحساب مصفّى بالكامل.*');
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

  const dir = directionFor(type, direction);
  const when = occurredAt || new Date().toISOString();

  run(
    `INSERT INTO ledger_entries
       (customer_id, customer_name, phone, type, direction, amount, ref, note, occurred_at, source, author)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'manual', ?)`,
    [String(customerId), customerName, phone, type, dir, round2(value), ref, note, when, actor],
  );

  const created = get('SELECT * FROM ledger_entries WHERE id = last_insert_rowid()');
  record({
    actor,
    action: 'ledger_add_entry',
    target: String(customerId),
    payload: { type, amount: round2(value), direction: dir, ref },
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
 * تصفية حساب العميل: تسجّل الحركة المقابلة للرصيد الحالي فيصبح صفراً.
 * إن كان الرصيد لصالح العميل تُسجَّل كإعادة مبلغ له، وإن كان عليه تُسجَّل كتحصيل منه.
 */
export async function settle(query, { note = null, method = 'نقداً' } = {}, actor = 'dashboard') {
  assertWritesAllowed();
  const stmt = await statement(query);
  if (!stmt.found) throw new HttpError(404, stmt.message);
  if (stmt.status === 'settled') {
    return { ok: true, alreadySettled: true, statement: stmt };
  }

  const direction = stmt.status === 'company_owes' ? 'debit' : 'credit';
  const amount = stmt.status === 'company_owes' ? stmt.toRefund : stmt.toCollect;
  const label =
    stmt.status === 'company_owes'
      ? `إعادة رصيد للعميل (${method})`
      : `تحصيل مستحقات من العميل (${method})`;

  addEntry(
    {
      customerId: stmt.customer.id,
      customerName: stmt.customer.name,
      phone: stmt.customer.phone,
      type: 'settlement',
      direction,
      amount,
      note: note ? `${label} — ${note}` : label,
      occurredAt: new Date().toISOString(),
    },
    actor,
  );

  record({
    actor,
    action: 'ledger_settle',
    target: stmt.customer.id,
    payload: { amount, direction, method },
  });

  const after = await statement(stmt.customer.id);
  return { ok: true, settledAmount: amount, direction, statement: after };
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
      net: stmt.totals.net,
      status: stmt.status,
      toRefund: stmt.toRefund,
      toCollect: stmt.toCollect,
      depositsHeld: stmt.totals.depositsHeld,
    });
  }
  return rows.sort((a, b) => Math.abs(b.net) - Math.abs(a.net));
}
