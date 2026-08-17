import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmpDb = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'callrent-acc-')), 'test.db');
process.env.DB_PATH = tmpDb;
process.env.EGANIS_DRIVER = 'mock';
process.env.WHATSAPP_DRIVER = 'mock';
process.env.ALLOW_WRITES = 'true';

const acc = await import('../src/core/accounting.js');

test('كشف الحساب يجمع التأمين والأجرة والدفعات من العقود', async () => {
  const stmt = await acc.statement('أحمد نصار');
  assert.equal(stmt.found, true);
  // عقدان: تأمين 3000 + 2500، أجرة 480 + 660، دفعات 300 + 660
  assert.equal(stmt.totals.credits, 3000 + 2500 + 300 + 660);
  assert.equal(stmt.totals.debits, 480 + 660);
  assert.equal(stmt.totals.net, stmt.totals.credits - stmt.totals.debits);
  assert.equal(stmt.status, 'company_owes');
  assert.equal(stmt.toRefund, stmt.totals.net);
  assert.equal(stmt.toCollect, 0);
});

test('الرصيد الجاري يتراكم بترتيب التاريخ وينتهي بالصافي', async () => {
  const stmt = await acc.statement('أحمد نصار');
  assert.equal(stmt.entries.at(-1).running, stmt.totals.net);
  const dates = stmt.entries.map((e) => e.date);
  assert.deepEqual(dates, [...dates].sort());
});

test('تكاليف الحادث تقلب الحساب إلى مطالبة على العميل', async () => {
  const before = await acc.statement('سامي عودة');
  assert.equal(before.status, 'company_owes');

  acc.addEntry(
    {
      customerId: before.customer.id,
      customerName: before.customer.name,
      type: 'damage',
      amount: before.totals.net + 500,
      ref: 'CR-2042',
      note: 'إصلاح بعد حادث',
    },
    'test',
  );

  const after = await acc.statement('سامي عودة');
  assert.equal(after.status, 'customer_owes');
  assert.equal(after.toCollect, 500);
  assert.equal(after.totals.damages, before.totals.net + 500);
});

test('التأمين المحفوظ = المستلم ناقص المُعاد', async () => {
  const stmt = await acc.statement('ليلى حجازي');
  assert.equal(stmt.totals.depositsHeld, stmt.totals.depositsIn - stmt.totals.depositsBack);

  acc.addEntry(
    { customerId: stmt.customer.id, type: 'deposit_refund', amount: 500, note: 'إعادة جزئية' },
    'test',
  );
  const after = await acc.statement('ليلى حجازي');
  assert.equal(after.totals.depositsBack, 500);
  assert.equal(after.totals.depositsHeld, stmt.totals.depositsIn - 500);
});

test('التصفية تُصفّر الرصيد وتُسجَّل كحركة مقابلة', async () => {
  const before = await acc.statement('ليلى حجازي');
  assert.notEqual(before.totals.net, 0);

  const result = await acc.settle('ليلى حجازي', { method: 'نقداً' }, 'test');
  assert.equal(result.statement.totals.net, 0);
  assert.equal(result.statement.status, 'settled');
  assert.equal(result.settledAmount, Math.abs(before.totals.net));

  const last = result.statement.entries.at(-1);
  assert.equal(last.type, 'settlement');
  assert.equal(last.direction, before.status === 'company_owes' ? 'debit' : 'credit');
});

test('إلغاء حركة يدوية يعيد الرصيد كما كان', async () => {
  const before = await acc.statement('أحمد نصار');
  const entry = acc.addEntry(
    { customerId: before.customer.id, type: 'fine', amount: 250, note: 'مخالفة' },
    'test',
  );
  const withFine = await acc.statement('أحمد نصار');
  assert.equal(withFine.totals.net, before.totals.net - 250);

  acc.voidEntry(entry.id, 'test');
  const after = await acc.statement('أحمد نصار');
  assert.equal(after.totals.net, before.totals.net);
});

test('نص الكشف يذكر المبلغ النهائي والجهة المستحقة', async () => {
  const stmt = await acc.statement('أحمد نصار');
  const text = acc.statementText(stmt);
  assert.match(text, /كشف حساب/);
  assert.match(text, /أحمد نصار/);
  assert.match(text, new RegExp(String(stmt.toRefund)));
  assert.match(text, /مستحقة لك/);
});

test('الأرصدة المفتوحة تستثني الحسابات المصفّاة', async () => {
  const rows = await acc.openBalances();
  assert.ok(rows.every((r) => r.status !== 'settled'));
  assert.ok(rows.some((r) => r.customer.name === 'أحمد نصار'));
});

test('رفض المبالغ غير الصالحة وأنواع الحركات المجهولة', () => {
  assert.throws(() => acc.addEntry({ customerId: 'C-501', type: 'damage', amount: -5 }, 'test'), /المبلغ/);
  assert.throws(() => acc.addEntry({ customerId: 'C-501', type: 'مجهول', amount: 5 }, 'test'), /نوع حركة/);
});
