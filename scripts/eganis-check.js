/**
 * فاحص الربط مع eganis — شغّله على خادمك بعد تعبئة config/eganis.json:
 *
 *   npm run eganis:check
 *
 * يجرّب تسجيل الدخول ثم كل عملية معرَّفة في الملف، ويقول لك بالضبط:
 * ما الذي نجح، وما الذي فشل ولماذا، وأي الحقول وصلت فارغة وتحتاج تعديل الخريطة.
 * لا يكتب شيئاً ولا ينفّذ أي أمر تعديل — قراءة فقط.
 */
import fs from 'node:fs';
import path from 'node:path';
import { config } from '../src/config.js';
import { eganis } from '../src/connectors/eganis/index.js';

const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const DIM = '\x1b[2m';
const OFF = '\x1b[0m';

const ok = (text) => console.log(`${GREEN}✔${OFF} ${text}`);
const bad = (text) => console.log(`${RED}✘${OFF} ${text}`);
const warn = (text) => console.log(`${YELLOW}!${OFF} ${text}`);
const dim = (text) => console.log(`${DIM}  ${text}${OFF}`);

/** الحقول التي يعتمد عليها التطبيق فعلياً في كل نوع سجل */
const REQUIRED = {
  contract: {
    must: ['no', 'customerName', 'startAt', 'endAt', 'status'],
    nice: ['customerId', 'phone', 'plate', 'total', 'paid', 'balance', 'deposit', 'currency'],
  },
  vehicle: { must: ['plate', 'status'], nice: ['make', 'model', 'year', 'group', 'branch'] },
  booking: { must: ['no', 'pickupAt'], nice: ['customerName', 'phone', 'group', 'branch', 'status'] },
  task: { must: ['type', 'at'], nice: ['ref', 'plate', 'driver', 'status'] },
  customer: { must: ['id', 'name'], nice: ['phone', 'idNumber', 'license'] },
  ledgerEntry: { must: ['type', 'amount'], nice: ['currency', 'ref', 'note', 'occurredAt'] },
  document: { must: ['id', 'name'], nice: ['kind', 'mime', 'contractNo', 'plate', 'customerId'] },
};

function checkFields(kind, rows) {
  const spec = REQUIRED[kind];
  if (!spec || !rows.length) return;
  const sample = rows[0];
  const missing = spec.must.filter((f) => sample[f] === undefined || sample[f] === null);
  const empty = spec.nice.filter((f) => sample[f] === undefined || sample[f] === null);

  if (missing.length) {
    bad(`   حقول أساسية ناقصة في ${kind}: ${missing.join(', ')} — عدّل maps.${kind} في config/eganis.json`);
  }
  if (empty.length) {
    warn(`   حقول اختيارية فارغة في ${kind}: ${empty.join(', ')}`);
  }
  if (kind === 'contract' && sample.currency === undefined) {
    warn('   لا يوجد حقل currency في العقود — ستُحسب كلها بالليرة. أضِف "currency" في maps.contract');
  }
  dim(`   عيّنة: ${JSON.stringify(sample).slice(0, 220)}…`);
}

async function tryCall(label, kind, fn) {
  const startedAt = Date.now();
  try {
    const result = await fn();
    const rows = Array.isArray(result) ? result : result ? [result] : [];
    ok(`${label} — ${rows.length} سجل (${Date.now() - startedAt} مللي ثانية)`);
    checkFields(kind, rows);
    return rows;
  } catch (err) {
    bad(`${label} — ${err.message}`);
    if (err.details) dim(String(err.details).slice(0, 300));
    return null;
  }
}

async function main() {
  console.log('\n=== فحص الربط مع eganis ===\n');
  console.log(`السائق: ${config.eganis.driver}`);
  console.log(`العنوان: ${config.eganis.baseUrl || '(غير محدّد)'}`);
  console.log(`نوع التوثيق: ${config.eganis.auth}\n`);

  if (config.eganis.driver === 'mock') {
    warn('السائق الحالي "mock" — بيانات تجريبية. اضبط EGANIS_DRIVER=api في .env للفحص الحقيقي.\n');
  }

  if (config.eganis.driver === 'api') {
    const file = path.resolve(process.cwd(), config.eganis.endpointsFile);
    if (!fs.existsSync(file)) {
      bad(`ملف المسارات غير موجود: ${file}`);
      dim('انسخ config/eganis.example.json إلى config/eganis.json ثم عبّئه من توثيق حسابك.');
      process.exit(1);
    }
    const profile = JSON.parse(fs.readFileSync(file, 'utf8'));
    const defined = Object.keys(profile.endpoints || {});
    ok(`ملف المسارات: ${defined.length} عملية معرَّفة`);
    dim(defined.join(' · '));
    console.log('');
  }

  const driver = eganis();

  const health = await driver.health();
  if (health.ok) ok('الاتصال وتسجيل الدخول');
  else {
    bad(`الاتصال: ${health.error}`);
    dim('تأكّد من EGANIS_BASE_URL و EGANIS_USERNAME/PASSWORD أو EGANIS_API_KEY، ومن مسار auth في ملف المسارات.');
  }
  console.log('');

  // ===== القراءة =====
  const contracts = await tryCall('العقود (listContracts)', 'contract', () => driver.listContracts({}));
  await tryCall('المركبات (listVehicles)', 'vehicle', () => driver.listVehicles({}));
  await tryCall('الحجوزات (listBookings)', 'booking', () => driver.listBookings({}));
  await tryCall('المهام (listTasks)', 'task', () => driver.listTasks({}));
  const customers = await tryCall('العملاء (searchCustomers)', 'customer', () =>
    driver.searchCustomers(''),
  );

  if (contracts?.length) {
    const first = contracts[0];
    await tryCall(`تفاصيل عقد (getContract: ${first.no || first.id})`, 'contract', () =>
      driver.getContract(first.no || first.id),
    );
  }

  // ===== كشف الحساب =====
  console.log('');
  if (typeof driver.listLedgerEntries === 'function') {
    const customerId = customers?.[0]?.id;
    if (customerId) {
      await tryCall(`حركات حساب عميل (listLedgerEntries: ${customerId})`, 'ledgerEntry', () =>
        driver.listLedgerEntries(customerId),
      );
    }
  } else {
    warn('listLedgerEntries غير معرَّف — ستُشتق حركات الحساب من العقود (تأمين + أجرة + مدفوع).');
    dim('إن وفّر حسابك مساراً لكشف الحساب فأضِفه، فهو أدق.');
  }

  // ===== المستندات =====
  if (typeof driver.listDocuments === 'function') {
    const docs = await tryCall('المستندات (listDocuments)', 'document', () => driver.listDocuments({}));
    if (docs?.length && typeof driver.downloadDocument === 'function') {
      await tryCall(`تنزيل مستند (${docs[0].name})`, null, async () => {
        const doc = await driver.downloadDocument(docs[0].id);
        return { name: doc.name, mime: doc.mime, size: doc.buffer?.length ?? 0 };
      });
    }
  } else {
    warn('listDocuments غير معرَّف — لن يستطيع المساعد إحضار العقود وصور المركبات.');
  }

  console.log('\n=== انتهى الفحص ===');
  console.log('كل سطر أحمر يحتاج تعديلاً في config/eganis.json أو في .env — أرسل لي المخرجات وأزبّطها.\n');
}

main().catch((err) => {
  bad(`فشل الفحص: ${err.message}`);
  process.exit(1);
});
