/**
 * طبقة العمليات: تجمع بيانات eganis في صورة جاهزة للتشغيل اليومي،
 * وتنفّذ الأوامر مع تسجيلها في سجل التدقيق.
 */
import { eganis } from '../connectors/eganis/index.js';
import { assertWritesAllowed } from '../config.js';
import { record } from './audit.js';
import * as fx from './fx.js';
import { all, run } from '../db.js';

/**
 * «اليوم» بتوقيت الشركة لا بتوقيت غرينتش: عقد ينتهي الساعة ٩ صباحاً في
 * إسطنبول يجب أن يظهر في إرجاعات اليوم، لا في اليوم السابق أو التالي.
 */
const localDay = (date) => {
  const pad = (n) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
};

const dayKey = (value) => {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : localDay(date);
};
const today = () => localDay(new Date());

/** لوحة اليوم: تسليمات، استرجاعات، متأخرات، أسطول، تنبيهات */
export async function overview() {
  const snap = await eganis().snapshot();
  const t = today();
  const now = Date.now();

  const contracts = snap.contracts || [];
  const vehicles = snap.vehicles || [];
  const bookings = snap.bookings || [];
  const tasks = snap.tasks || [];

  const overdue = contracts.filter(
    (c) => c.status === 'overdue' || (c.status === 'open' && new Date(c.endAt).getTime() < now),
  );
  const dueToday = contracts.filter((c) => c.status === 'open' && dayKey(c.endAt) === t);
  const pickupsToday = bookings.filter((b) => dayKey(b.pickupAt) === t && b.status !== 'cancelled');
  const openTasksToday = tasks.filter((x) => x.status !== 'done' && dayKey(x.at) === t);
  const lateTasks = tasks.filter((x) => x.status !== 'done' && new Date(x.at).getTime() < now);
  const unpaid = contracts.filter((c) => c.status !== 'closed' && Number(c.balance) > 0);

  const fleet = vehicles.reduce((acc, v) => {
    acc[v.status] = (acc[v.status] || 0) + 1;
    return acc;
  }, {});

  // الأرصدة غير المحصّلة تُجمَع لكل عملة على حدة — لا تُخلط الليرة بالدولار
  const unpaidByCurrency = { TRY: 0, USD: 0 };
  for (const c of unpaid) {
    unpaidByCurrency[fx.normalizeCurrency(c.currency)] += Number(c.balance || 0);
  }
  for (const key of Object.keys(unpaidByCurrency)) {
    unpaidByCurrency[key] = Math.round(unpaidByCurrency[key] * 100) / 100;
  }

  const alerts = [];
  if (overdue.length) alerts.push({ level: 'high', text: `${overdue.length} عقد متأخر عن موعد الإرجاع` });
  if (lateTasks.length) alerts.push({ level: 'high', text: `${lateTasks.length} مهمة تجاوزت وقتها` });
  if (unpaid.length) {
    alerts.push({
      level: 'medium',
      text: `رصيد غير محصّل: ${fx.dual(unpaidByCurrency)} على ${unpaid.length} عقد`,
    });
  }
  if ((fleet.available || 0) === 0) alerts.push({ level: 'high', text: 'لا توجد مركبات متاحة حالياً' });

  return {
    date: t,
    counters: {
      contractsOpen: contracts.filter((c) => c.status === 'open').length,
      overdue: overdue.length,
      dueToday: dueToday.length,
      pickupsToday: pickupsToday.length,
      tasksToday: openTasksToday.length,
      vehiclesAvailable: fleet.available || 0,
      vehiclesRented: fleet.rented || 0,
      vehiclesMaintenance: fleet.maintenance || 0,
      unpaidBalance: unpaidByCurrency,
      unpaidBalanceText: fx.dual(unpaidByCurrency),
    },
    alerts,
    overdue,
    dueToday,
    pickupsToday,
    tasksToday: openTasksToday,
  };
}

export const listVehicles = (filter) => eganis().listVehicles(filter);
export const listContracts = (filter) => eganis().listContracts(filter);
export const listBookings = (filter) => eganis().listBookings(filter);
export const listTasks = (filter) => eganis().listTasks(filter);
export const searchCustomers = (q) => eganis().searchCustomers(q);

export async function getContract(id) {
  const contract = await eganis().getContract(id);
  const notes = all('SELECT * FROM notes WHERE ref_type = ? AND ref_id = ? ORDER BY id DESC', [
    'contract',
    String(contract.no || contract.id),
  ]);
  return { ...contract, notes };
}

/** ملف العميل: بياناته + عقوده — يُستخدم عند الرد على واتساب */
export async function customerContext(phone) {
  const driver = eganis();
  const customer = await driver.findCustomerByPhone(phone);
  const contracts = await driver.listContracts({ q: phone });
  return { customer, contracts };
}

// ===== الأوامر (تُسجَّل جميعها في سجل التدقيق) =====

async function command(actor, action, target, payload, fn) {
  assertWritesAllowed();
  try {
    const result = await fn();
    record({ actor, action, target, payload, result, ok: true });
    return result;
  } catch (err) {
    record({ actor, action, target, payload, result: { error: err.message }, ok: false });
    throw err;
  }
}

export const extendContract = (id, days, actor = 'api') =>
  command(actor, 'extend_contract', id, { days }, () => eganis().extendContract(id, days));

export const closeContract = (id, opts = {}, actor = 'api') =>
  command(actor, 'close_contract', id, opts, () => eganis().closeContract(id, opts));

export const setVehicleStatus = (id, status, note, actor = 'api') =>
  command(actor, 'set_vehicle_status', id, { status, note }, () =>
    eganis().setVehicleStatus(id, status, note),
  );

export const assignTask = (id, driver, actor = 'api') =>
  command(actor, 'assign_task', id, { driver }, () => eganis().assignTask(id, driver));

export const completeTask = (id, note, actor = 'api') =>
  command(actor, 'complete_task', id, { note }, () => eganis().completeTask(id, note));

export function addNote({ refType, refId, body, author = 'dashboard' }) {
  run('INSERT INTO notes (ref_type, ref_id, body, author) VALUES (?, ?, ?, ?)', [
    refType,
    String(refId),
    body,
    author,
  ]);
  record({ actor: author, action: 'add_note', target: `${refType}:${refId}`, payload: { body } });
  return { ok: true };
}

export const listNotes = (refType, refId) =>
  all('SELECT * FROM notes WHERE ref_type = ? AND ref_id = ? ORDER BY id DESC', [
    refType,
    String(refId),
  ]);
