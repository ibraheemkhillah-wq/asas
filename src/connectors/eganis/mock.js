/**
 * سائق تجريبي (mock) لـ eganis — بيانات وهمية للتطوير والعرض.
 * يطبّق نفس الواجهة التي يطبّقها سائق الـ API وسائق المتصفح.
 */
import { HttpError } from '../../lib/http.js';

const day = 86400000;
const iso = (d) => new Date(d).toISOString();
const at = (offsetDays, hour = 9) => {
  const d = new Date();
  d.setHours(hour, 0, 0, 0);
  return iso(d.getTime() + offsetDays * day);
};
const todayKey = () => new Date().toISOString().slice(0, 10);
const dayKey = (value) => new Date(value).toISOString().slice(0, 10);

const state = {
  vehicles: [
    { id: 'V-1001', plate: '1234-567', make: 'هيونداي', model: 'أكسنت', year: 2023, group: 'اقتصادي', status: 'rented', branch: 'الخليل', odometer: 48210 },
    { id: 'V-1002', plate: '2345-678', make: 'كيا', model: 'ريو', year: 2022, group: 'اقتصادي', status: 'available', branch: 'الخليل', odometer: 61340 },
    { id: 'V-1003', plate: '3456-789', make: 'تويوتا', model: 'كورولا', year: 2024, group: 'متوسط', status: 'rented', branch: 'رام الله', odometer: 15120 },
    { id: 'V-1004', plate: '4567-890', make: 'شيفروليه', model: 'كابتيفا', year: 2023, group: 'SUV', status: 'maintenance', branch: 'الخليل', odometer: 88900 },
    { id: 'V-1005', plate: '5678-901', make: 'سكودا', model: 'أوكتافيا', year: 2024, group: 'متوسط', status: 'available', branch: 'رام الله', odometer: 9400 },
    { id: 'V-1006', plate: '6789-012', make: 'هيونداي', model: 'توسان', year: 2025, group: 'SUV', status: 'rented', branch: 'الخليل', odometer: 4300 },
  ],
  customers: [
    { id: 'C-501', name: 'أحمد نصار', phone: '970599111222', idNumber: '901234567', license: 'DL-88231', blacklisted: false },
    { id: 'C-502', name: 'سامي عودة', phone: '970598333444', idNumber: '902345678', license: 'DL-77120', blacklisted: false },
    { id: 'C-503', name: 'ليلى حجازي', phone: '970569555666', idNumber: '903456789', license: 'DL-66019', blacklisted: false },
    { id: 'C-504', name: 'مروان قاسم', phone: '970592777888', idNumber: '904567890', license: 'DL-55908', blacklisted: true },
  ],
  contracts: [
    {
      id: 'K-2041', no: 'CR-2041', customerId: 'C-501', customerName: 'أحمد نصار', phone: '970599111222',
      vehicleId: 'V-1001', plate: '1234-567', startAt: at(-4, 10), endAt: at(0, 18), status: 'open',
      dailyRate: 120, days: 4, total: 480, paid: 300, balance: 180, branchOut: 'الخليل', branchIn: 'الخليل',
    },
    {
      id: 'K-2042', no: 'CR-2042', customerId: 'C-502', customerName: 'سامي عودة', phone: '970598333444',
      vehicleId: 'V-1003', plate: '3456-789', startAt: at(-9, 12), endAt: at(-1, 12), status: 'overdue',
      dailyRate: 150, days: 8, total: 1200, paid: 600, balance: 600, branchOut: 'رام الله', branchIn: 'رام الله',
    },
    {
      id: 'K-2043', no: 'CR-2043', customerId: 'C-503', customerName: 'ليلى حجازي', phone: '970569555666',
      vehicleId: 'V-1006', plate: '6789-012', startAt: at(-1, 9), endAt: at(5, 9), status: 'open',
      dailyRate: 210, days: 6, total: 1260, paid: 1260, balance: 0, branchOut: 'الخليل', branchIn: 'الخليل',
    },
    {
      id: 'K-2040', no: 'CR-2040', customerId: 'C-501', customerName: 'أحمد نصار', phone: '970599111222',
      vehicleId: 'V-1002', plate: '2345-678', startAt: at(-20, 10), endAt: at(-14, 10), status: 'closed',
      dailyRate: 110, days: 6, total: 660, paid: 660, balance: 0, branchOut: 'الخليل', branchIn: 'الخليل',
    },
  ],
  bookings: [
    { id: 'B-771', no: 'BK-771', customerName: 'رامي أبو دية', phone: '970597123456', group: 'اقتصادي', pickupAt: at(0, 16), dropoffAt: at(3, 16), branch: 'الخليل', status: 'confirmed' },
    { id: 'B-772', no: 'BK-772', customerName: 'نور صبري', phone: '970568999111', group: 'SUV', pickupAt: at(1, 11), dropoffAt: at(6, 11), branch: 'رام الله', status: 'new' },
    { id: 'B-773', no: 'BK-773', customerName: 'خالد سليم', phone: '970599888777', group: 'متوسط', pickupAt: at(0, 20), dropoffAt: at(2, 20), branch: 'الخليل', status: 'confirmed' },
  ],
  tasks: [
    { id: 'T-9001', type: 'delivery', at: at(0, 16), ref: 'BK-771', plate: '2345-678', location: 'الخليل - المكتب', driver: 'محمد', status: 'pending' },
    { id: 'T-9002', type: 'pickup', at: at(0, 18), ref: 'CR-2041', plate: '1234-567', location: 'الخليل - عين سارة', driver: null, status: 'pending' },
    { id: 'T-9003', type: 'pickup', at: at(-1, 12), ref: 'CR-2042', plate: '3456-789', location: 'رام الله - المصيون', driver: 'سامر', status: 'pending' },
    { id: 'T-9004', type: 'maintenance', at: at(0, 9), ref: 'V-1004', plate: '4567-890', location: 'كراج الشركة', driver: 'ورشة', status: 'pending' },
  ],
};

const clone = (v) => JSON.parse(JSON.stringify(v));
const matches = (haystack, q) =>
  !q || String(haystack ?? '').toLowerCase().includes(String(q).toLowerCase());

function findContract(idOrNo) {
  const c = state.contracts.find(
    (x) => x.id === idOrNo || x.no === idOrNo || x.plate === idOrNo,
  );
  if (!c) throw new HttpError(404, `لم يتم العثور على العقد: ${idOrNo}`);
  return c;
}

function findVehicle(idOrPlate) {
  const v = state.vehicles.find((x) => x.id === idOrPlate || x.plate === idOrPlate);
  if (!v) throw new HttpError(404, `لم يتم العثور على المركبة: ${idOrPlate}`);
  return v;
}

export function createMockDriver() {
  return {
    name: 'mock',

    async health() {
      return { ok: true, driver: 'mock', note: 'بيانات تجريبية — لا يوجد اتصال فعلي بـ eganis' };
    },

    async listVehicles({ status, branch, q } = {}) {
      return clone(
        state.vehicles.filter(
          (v) =>
            (!status || v.status === status) &&
            (!branch || v.branch === branch) &&
            (!q || matches(v.plate, q) || matches(v.model, q) || matches(v.make, q)),
        ),
      );
    },

    async listContracts({ status, date, q } = {}) {
      return clone(
        state.contracts.filter((c) => {
          if (status && c.status !== status) return false;
          if (date && dayKey(c.startAt) !== date && dayKey(c.endAt) !== date) return false;
          if (q && !(matches(c.no, q) || matches(c.customerName, q) || matches(c.phone, q) || matches(c.plate, q)))
            return false;
          return true;
        }),
      );
    },

    async getContract(idOrNo) {
      return clone(findContract(idOrNo));
    },

    async listBookings({ date, status } = {}) {
      return clone(
        state.bookings.filter(
          (b) => (!status || b.status === status) && (!date || dayKey(b.pickupAt) === date),
        ),
      );
    },

    async listTasks({ date, type } = {}) {
      return clone(
        state.tasks.filter(
          (t) => (!type || t.type === type) && (!date || dayKey(t.at) === date),
        ),
      );
    },

    async searchCustomers(q) {
      return clone(
        state.customers.filter(
          (c) => matches(c.name, q) || matches(c.phone, q) || matches(c.idNumber, q),
        ),
      );
    },

    async findCustomerByPhone(phone) {
      const digits = String(phone).replace(/\D/g, '');
      const c = state.customers.find((x) => digits.endsWith(x.phone.slice(-9)));
      return c ? clone(c) : null;
    },

    // ===== أوامر التعديل =====

    async extendContract(idOrNo, days) {
      const c = findContract(idOrNo);
      const added = Number(days);
      if (!Number.isFinite(added) || added <= 0) throw new HttpError(400, 'عدد الأيام غير صالح');
      c.endAt = iso(new Date(c.endAt).getTime() + added * day);
      c.days += added;
      c.total += added * c.dailyRate;
      c.balance = c.total - c.paid;
      if (c.status === 'overdue') c.status = 'open';
      return clone(c);
    },

    async closeContract(idOrNo, { odometer, notes } = {}) {
      const c = findContract(idOrNo);
      c.status = 'closed';
      c.closedAt = iso(Date.now());
      if (notes) c.closingNotes = notes;
      const v = state.vehicles.find((x) => x.id === c.vehicleId);
      if (v) {
        v.status = 'available';
        if (Number.isFinite(Number(odometer))) v.odometer = Number(odometer);
      }
      return clone(c);
    },

    async setVehicleStatus(idOrPlate, status, note) {
      const allowed = ['available', 'rented', 'maintenance', 'out_of_service'];
      if (!allowed.includes(status)) {
        throw new HttpError(400, `حالة غير مدعومة. المسموح: ${allowed.join(', ')}`);
      }
      const v = findVehicle(idOrPlate);
      v.status = status;
      if (note) v.note = note;
      return clone(v);
    },

    async assignTask(taskId, driver) {
      const t = state.tasks.find((x) => x.id === taskId);
      if (!t) throw new HttpError(404, `لم يتم العثور على المهمة: ${taskId}`);
      t.driver = driver;
      return clone(t);
    },

    async completeTask(taskId, note) {
      const t = state.tasks.find((x) => x.id === taskId);
      if (!t) throw new HttpError(404, `لم يتم العثور على المهمة: ${taskId}`);
      t.status = 'done';
      if (note) t.note = note;
      return clone(t);
    },

    /** يستخدمه المزامن لبناء لوحة اليوم */
    async snapshot() {
      const today = todayKey();
      return {
        today,
        vehicles: clone(state.vehicles),
        contracts: clone(state.contracts),
        bookings: clone(state.bookings),
        tasks: clone(state.tasks),
      };
    },
  };
}
