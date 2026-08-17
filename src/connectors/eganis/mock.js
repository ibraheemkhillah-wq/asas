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
    { id: 'V-1001', plate: '1234-567', make: 'هيونداي', model: 'أكسنت', year: 2023, group: 'اقتصادي', status: 'rented', branch: 'تقسيم', odometer: 48210 },
    { id: 'V-1002', plate: '2345-678', make: 'كيا', model: 'ريو', year: 2022, group: 'اقتصادي', status: 'available', branch: 'تقسيم', odometer: 61340 },
    { id: 'V-1003', plate: '3456-789', make: 'تويوتا', model: 'كورولا', year: 2024, group: 'متوسط', status: 'rented', branch: 'قاضي كوي', odometer: 15120 },
    { id: 'V-1004', plate: '4567-890', make: 'شيفروليه', model: 'كابتيفا', year: 2023, group: 'SUV', status: 'maintenance', branch: 'تقسيم', odometer: 88900 },
    { id: 'V-1005', plate: '5678-901', make: 'سكودا', model: 'أوكتافيا', year: 2024, group: 'متوسط', status: 'available', branch: 'قاضي كوي', odometer: 9400 },
    { id: 'V-1006', plate: '6789-012', make: 'هيونداي', model: 'توسان', year: 2025, group: 'SUV', status: 'rented', branch: 'تقسيم', odometer: 4300 },
  ],
  customers: [
    { id: 'C-501', name: 'أحمد نصار', phone: '905321114422', idNumber: '901234567', license: 'DL-88231', blacklisted: false },
    { id: 'C-502', name: 'سامي عودة', phone: '905337778899', idNumber: '902345678', license: 'DL-77120', blacklisted: false },
    { id: 'C-503', name: 'ليلى حجازي', phone: '905445556677', idNumber: '903456789', license: 'DL-66019', blacklisted: false },
    { id: 'C-504', name: 'مروان قاسم', phone: '905396663311', idNumber: '904567890', license: 'DL-55908', blacklisted: true },
  ],
  contracts: [
    {
      id: 'K-2041', no: 'CR-2041', customerId: 'C-501', customerName: 'أحمد نصار', phone: '905321114422',
      vehicleId: 'V-1001', plate: '1234-567', startAt: at(-4, 10), endAt: at(0, 18), status: 'open',
      dailyRate: 120, days: 4, total: 480, paid: 300, balance: 180, deposit: 3000, branchOut: 'تقسيم', branchIn: 'تقسيم',
    },
    {
      id: 'K-2042', no: 'CR-2042', customerId: 'C-502', customerName: 'سامي عودة', phone: '905337778899',
      vehicleId: 'V-1003', plate: '3456-789', startAt: at(-9, 12), endAt: at(-1, 12), status: 'overdue',
      dailyRate: 150, days: 8, total: 1200, paid: 600, balance: 600, deposit: 3000, branchOut: 'قاضي كوي', branchIn: 'قاضي كوي',
    },
    {
      id: 'K-2043', no: 'CR-2043', customerId: 'C-503', customerName: 'ليلى حجازي', phone: '905445556677',
      vehicleId: 'V-1006', plate: '6789-012', startAt: at(-1, 9), endAt: at(5, 9), status: 'open',
      dailyRate: 210, days: 6, total: 1260, paid: 1260, balance: 0, deposit: 2000, branchOut: 'تقسيم', branchIn: 'تقسيم',
    },
    {
      id: 'K-2040', no: 'CR-2040', customerId: 'C-501', customerName: 'أحمد نصار', phone: '905321114422',
      vehicleId: 'V-1002', plate: '2345-678', startAt: at(-20, 10), endAt: at(-14, 10), status: 'closed',
      dailyRate: 110, days: 6, total: 660, paid: 660, balance: 0, deposit: 2500, branchOut: 'تقسيم', branchIn: 'تقسيم',
    },
  ],
  bookings: [
    { id: 'B-771', no: 'BK-771', customerName: 'رامي أبو دية', phone: '905301234567', group: 'اقتصادي', pickupAt: at(0, 16), dropoffAt: at(3, 16), branch: 'تقسيم', status: 'confirmed' },
    { id: 'B-772', no: 'BK-772', customerName: 'نور صبري', phone: '905389990011', group: 'SUV', pickupAt: at(1, 11), dropoffAt: at(6, 11), branch: 'قاضي كوي', status: 'new' },
    { id: 'B-773', no: 'BK-773', customerName: 'خالد سليم', phone: '905358887766', group: 'متوسط', pickupAt: at(0, 20), dropoffAt: at(2, 20), branch: 'تقسيم', status: 'confirmed' },
  ],
  tasks: [
    { id: 'T-9001', type: 'delivery', at: at(0, 16), ref: 'BK-771', plate: '2345-678', location: 'تقسيم — المكتب', driver: 'محمد', status: 'pending' },
    { id: 'T-9002', type: 'pickup', at: at(0, 18), ref: 'CR-2041', plate: '1234-567', location: 'مطار صبيحة كوكجن — الوصول', driver: null, status: 'pending' },
    { id: 'T-9003', type: 'pickup', at: at(-1, 12), ref: 'CR-2042', plate: '3456-789', location: 'قاضي كوي — الميناء', driver: 'سامر', status: 'pending' },
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
          (c) =>
            matches(c.id, q) ||
            matches(c.name, q) ||
            matches(c.phone, q) ||
            matches(c.idNumber, q),
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

    // ===== المستندات والصور =====
    // في الوضع التجريبي تُولَّد نماذج SVG بسيطة. بعد الربط الفعلي تأتي الملفات
    // الأصلية من eganis (PDF / JPEG) كما هي.

    async listDocuments({ customerId, contractNo, plate, type } = {}) {
      const docs = [];

      for (const c of state.contracts) {
        if (customerId && c.customerId !== customerId) continue;
        if (contractNo && c.no !== contractNo) continue;
        if (plate && c.plate !== plate) continue;
        docs.push({
          id: `doc-${c.no}-contract`,
          name: `عقد الإيجار ${c.no}.svg`,
          kind: 'contract',
          mime: 'image/svg+xml',
          ref: c.no,
          contractNo: c.no,
          plate: c.plate,
          customerId: c.customerId,
          title: `عقد إيجار ${c.no} — ${c.customerName}`,
        });
      }

      for (const v of state.vehicles) {
        if (plate && v.plate !== plate) continue;
        if (customerId || contractNo) {
          const linked = state.contracts.some(
            (c) =>
              c.plate === v.plate && (c.customerId === customerId || c.no === contractNo),
          );
          if (!linked) continue;
        }
        docs.push({
          id: `doc-${v.plate}-insurance`,
          name: `بوليصة تأمين ${v.plate}.svg`,
          kind: 'insurance',
          mime: 'image/svg+xml',
          ref: v.plate,
          plate: v.plate,
          title: `تأمين المركبة ${v.plate} — ${v.make} ${v.model}`,
        });
        docs.push({
          id: `doc-${v.plate}-photo`,
          name: `صورة المركبة ${v.plate}.svg`,
          kind: 'vehicle_photo',
          mime: 'image/svg+xml',
          ref: v.plate,
          plate: v.plate,
          title: `${v.make} ${v.model} ${v.year} — ${v.plate}`,
        });
      }

      return type ? docs.filter((d) => d.kind === type) : docs;
    },

    async downloadDocument(id) {
      const doc = (await this.listDocuments({})).find((d) => d.id === id);
      if (!doc) throw new HttpError(404, `لا يوجد مستند بالمعرّف ${id}`);

      const palette = {
        contract: '#1B2A56',
        insurance: '#0f7a51',
        vehicle_photo: '#334366',
      }[doc.kind] || '#1B2A56';

      const details = [];
      if (doc.contractNo) {
        const c = state.contracts.find((x) => x.no === doc.contractNo);
        if (c) {
          details.push(`العميل: ${c.customerName}`, `المركبة: ${c.plate}`,
            `من ${String(c.startAt).slice(0, 10)} إلى ${String(c.endAt).slice(0, 10)}`,
            `الأجرة اليومية: ${c.dailyRate} ₺ · التأمين: ${c.deposit || 0} ₺`);
        }
      } else if (doc.plate) {
        const v = state.vehicles.find((x) => x.plate === doc.plate);
        if (v) details.push(`${v.make} ${v.model} ${v.year}`, `الفئة: ${v.group}`, `الفرع: ${v.branch}`);
      }

      const rows = details
        .map((line, i) => `<text x="60" y="${230 + i * 44}" font-size="26" fill="#1b2a56">${line}</text>`)
        .join('');

      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 560" font-family="Tahoma, sans-serif" direction="rtl">
  <rect width="800" height="560" fill="#ffffff"/>
  <rect width="800" height="120" fill="${palette}"/>
  <text x="740" y="55" font-size="30" fill="#ffffff" text-anchor="end" font-weight="bold">CALL &amp; RENT</text>
  <text x="740" y="92" font-size="20" fill="#c9d4ec" text-anchor="end">${doc.title}</text>
  <text x="740" y="180" font-size="22" fill="#5a6478" text-anchor="end">${doc.name}</text>
  ${rows}
  <rect x="40" y="470" width="720" height="50" rx="10" fill="#f3f5fa"/>
  <text x="400" y="502" font-size="20" fill="#96650a" text-anchor="middle">نموذج تجريبي — بعد ربط eganis يصل الملف الأصلي</text>
</svg>`;

      return { name: doc.name, mime: 'image/svg+xml', buffer: Buffer.from(svg, 'utf8'), meta: doc };
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
