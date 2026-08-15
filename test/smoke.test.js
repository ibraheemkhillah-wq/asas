import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

// قاعدة بيانات مؤقتة لكل تشغيل اختبار
const tmpDb = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'callrent-')), 'test.db');
process.env.DB_PATH = tmpDb;
process.env.EGANIS_DRIVER = 'mock';
process.env.WHATSAPP_DRIVER = 'mock';
process.env.ALLOW_WRITES = 'true';

const ops = await import('../src/core/ops.js');
const inbox = await import('../src/core/inbox.js');

test('لوحة اليوم تعيد العدّادات والتنبيهات', async () => {
  const data = await ops.overview();
  assert.ok(data.date);
  assert.equal(typeof data.counters.vehiclesAvailable, 'number');
  assert.ok(Array.isArray(data.alerts));
  assert.ok(data.counters.overdue >= 1, 'يفترض وجود عقد متأخر في البيانات التجريبية');
});

test('تمديد عقد يزيد المدة ويُسجَّل في سجل التدقيق', async () => {
  const before = await ops.getContract('CR-2041');
  const after = await ops.extendContract('CR-2041', 2, 'test');
  assert.equal(after.days, before.days + 2);
  const { recentAudit } = await import('../src/core/audit.js');
  const entry = recentAudit(5).find((r) => r.action === 'extend_contract');
  assert.ok(entry && entry.ok);
});

test('إغلاق عقد يعيد المركبة إلى الأسطول', async () => {
  const contract = await ops.closeContract('CR-2043', { odometer: 5000 }, 'test');
  assert.equal(contract.status, 'closed');
  const vehicles = await ops.listVehicles({ status: 'available' });
  assert.ok(vehicles.some((v) => v.id === contract.vehicleId));
});

test('رسالة واردة تُنشئ محادثة ورسالة', () => {
  const { conversation } = inbox.recordInbound({
    phone: '970599111222',
    name: 'أحمد',
    body: 'مرحبا',
  });
  const messages = inbox.getMessages(conversation.id);
  assert.equal(messages.at(-1).body, 'مرحبا');
  assert.equal(messages.at(-1).direction, 'in');
});

test('الردود المدرَّبة تُضاف وتُقرأ', () => {
  inbox.addTemplate({ intent: 'اختبار', reply: 'رد اختباري' });
  const templates = inbox.listTemplates({ activeOnly: true });
  assert.ok(templates.some((t) => t.intent === 'اختبار'));
});

test('إرسال رسالة عبر سائق المحاكاة يُسجَّل كمُرسلة', async () => {
  const { conversation } = inbox.recordInbound({ phone: '970598333444', body: 'استفسار' });
  await inbox.sendMessage(conversation.id, 'أهلاً بك', 'test');
  const messages = inbox.getMessages(conversation.id);
  assert.equal(messages.at(-1).status, 'sent');
  assert.equal(messages.at(-1).direction, 'out');
});
