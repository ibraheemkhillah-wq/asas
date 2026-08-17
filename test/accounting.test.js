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
// سعر ثابت أثناء الاختبار حتى تكون المكافئات قابلة للتحقق
process.env.FX_MODE = 'manual';
process.env.FX_USD_TRY = '40';

const acc = await import('../src/core/accounting.js');

// أحمد نصار: عقد بالليرة (CR-2041) وعقد بالدولار (CR-2040)
const AHMAD_TRY = { credits: 3000 + 300, debits: 480 };
const AHMAD_USD = { credits: 200 + 210, debits: 210 };

test('كشف الحساب يفصل الليرة عن الدولار ولا يخلطهما', async () => {
  const stmt = await acc.statement('أحمد نصار');
  assert.equal(stmt.found, true);

  assert.equal(stmt.byCurrency.TRY.credits, AHMAD_TRY.credits);
  assert.equal(stmt.byCurrency.TRY.debits, AHMAD_TRY.debits);
  assert.equal(stmt.net.TRY, AHMAD_TRY.credits - AHMAD_TRY.debits);

  assert.equal(stmt.byCurrency.USD.credits, AHMAD_USD.credits);
  assert.equal(stmt.byCurrency.USD.debits, AHMAD_USD.debits);
  assert.equal(stmt.net.USD, AHMAD_USD.credits - AHMAD_USD.debits);

  assert.equal(stmt.status, 'company_owes');
  assert.deepEqual(stmt.toRefund, { TRY: stmt.net.TRY, USD: stmt.net.USD });
  assert.deepEqual(stmt.toCollect, { TRY: 0, USD: 0 });
});

test('العرض المزدوج يظهر المبلغين بالصيغة «ليرة / دولار»', async () => {
  const stmt = await acc.statement('أحمد نصار');
  assert.match(stmt.netText, /₺/);
  assert.match(stmt.netText, /\$/);
  assert.match(stmt.netText, / \/ /);
});

test('المكافئ الإجمالي يُحسب بسعر الصرف لحظة الكشف', async () => {
  const stmt = await acc.statement('أحمد نصار');
  assert.equal(stmt.fx.rate, 40);
  assert.equal(stmt.combined.inTRY, stmt.net.TRY + stmt.net.USD * 40);
  assert.equal(stmt.combined.inUSD, Math.round((stmt.net.TRY / 40 + stmt.net.USD) * 100) / 100);
});

test('الرصيد الجاري يتراكم لكل عملة على حدة', async () => {
  const stmt = await acc.statement('أحمد نصار');
  const lastTry = stmt.entries.filter((e) => e.currency === 'TRY').at(-1);
  const lastUsd = stmt.entries.filter((e) => e.currency === 'USD').at(-1);
  assert.equal(lastTry.running, stmt.net.TRY);
  assert.equal(lastUsd.running, stmt.net.USD);

  const dates = stmt.entries.map((e) => e.date);
  assert.deepEqual(dates, [...dates].sort());
});

test('حركة بالدولار لا تغيّر رصيد الليرة', async () => {
  const before = await acc.statement('أحمد نصار');
  const entry = acc.addEntry(
    { customerId: before.customer.id, type: 'fine', amount: 20, currency: 'USD', note: 'مخالفة' },
    'test',
  );
  const after = await acc.statement('أحمد نصار');
  assert.equal(after.net.TRY, before.net.TRY);
  assert.equal(after.net.USD, before.net.USD - 20);

  acc.voidEntry(entry.id, 'test');
  const restored = await acc.statement('أحمد نصار');
  assert.equal(restored.net.USD, before.net.USD);
});

test('تكاليف الحادث تقلب الحساب إلى مطالبة على العميل', async () => {
  const before = await acc.statement('سامي عودة');
  assert.equal(before.status, 'company_owes');
  assert.equal(before.net.USD, 0);

  acc.addEntry(
    {
      customerId: before.customer.id,
      customerName: before.customer.name,
      type: 'damage',
      amount: before.net.TRY + 500,
      currency: 'TRY',
      ref: 'CR-2042',
      note: 'إصلاح بعد حادث',
    },
    'test',
  );

  const after = await acc.statement('سامي عودة');
  assert.equal(after.status, 'customer_owes');
  assert.equal(after.toCollect.TRY, 500);
  assert.equal(after.byCurrency.TRY.damages, before.net.TRY + 500);
});

test('التأمين المحفوظ = المستلم ناقص المُعاد، بعملة العقد', async () => {
  const stmt = await acc.statement('ليلى حجازي');
  // عقد ليلى بالدولار بالكامل
  assert.equal(stmt.byCurrency.USD.depositsIn, 150);
  assert.equal(stmt.byCurrency.TRY.entries, 0);
  assert.equal(
    stmt.byCurrency.USD.depositsHeld,
    stmt.byCurrency.USD.depositsIn - stmt.byCurrency.USD.depositsBack,
  );

  acc.addEntry(
    {
      customerId: stmt.customer.id,
      type: 'deposit_refund',
      amount: 50,
      currency: 'USD',
      note: 'إعادة جزئية',
    },
    'test',
  );
  const after = await acc.statement('ليلى حجازي');
  assert.equal(after.byCurrency.USD.depositsBack, 50);
  assert.equal(after.byCurrency.USD.depositsHeld, 150 - 50);
});

test('التصفية تُصفّر كل عملة بحركة مقابلة بعملتها', async () => {
  // رصيد بالعملتين معاً
  const target = await acc.statement('ليلى حجازي');
  acc.addEntry(
    { customerId: target.customer.id, type: 'payment', amount: 800, currency: 'TRY', note: 'دفعة' },
    'test',
  );

  const before = await acc.statement('ليلى حجازي');
  assert.notEqual(before.net.TRY, 0);
  assert.notEqual(before.net.USD, 0);

  const result = await acc.settle('ليلى حجازي', { method: 'نقداً' }, 'test');
  assert.equal(result.statement.net.TRY, 0);
  assert.equal(result.statement.net.USD, 0);
  assert.equal(result.statement.status, 'settled');
  assert.equal(result.settledAmount.TRY, Math.abs(before.net.TRY));
  assert.equal(result.settledAmount.USD, Math.abs(before.net.USD));

  const settlements = result.statement.entries.filter((e) => e.type === 'settlement');
  assert.equal(settlements.length, 2);
  assert.deepEqual(
    settlements.map((e) => e.currency).sort(),
    ['TRY', 'USD'],
  );
});

test('يمكن تصفية عملة واحدة فقط وترك الأخرى', async () => {
  const before = await acc.statement('أحمد نصار');
  assert.notEqual(before.net.TRY, 0);
  assert.notEqual(before.net.USD, 0);

  const result = await acc.settle('أحمد نصار', { currency: 'USD' }, 'test');
  assert.equal(result.settled.length, 1);
  assert.equal(result.settled[0].currency, 'USD');
  assert.equal(result.statement.net.USD, 0);
  assert.equal(result.statement.net.TRY, before.net.TRY);
});

test('الدفع بعملة أخرى يوثَّق في الملاحظة مع بقاء الحركة بعملة الرصيد', async () => {
  const before = await acc.statement('أحمد نصار');
  const result = await acc.settle('أحمد نصار', { currency: 'TRY', payIn: 'USD' }, 'test');
  const entry = result.statement.entries.at(-1);
  assert.equal(entry.currency, 'TRY');
  assert.equal(entry.debit, Math.abs(before.net.TRY));
  assert.match(entry.note, /\$/);
});

test('نص الكشف يعرض المبلغ بالعملتين ويذكر سعر الصرف', async () => {
  const stmt = await acc.statement('سامي عودة');
  const text = acc.statementText(stmt);
  assert.match(text, /كشف حساب/);
  assert.match(text, /سامي عودة/);
  assert.match(text, /سعر الصرف المعتمد/);
  assert.match(text, /مستحقة علينا منك|مستحقة لك/);
});

test('الأرصدة المفتوحة تعرض كل عملة وتستثني المصفّاة', async () => {
  const rows = await acc.openBalances();
  assert.ok(rows.every((r) => r.status !== 'settled'));
  assert.ok(rows.every((r) => typeof r.net.TRY === 'number' && typeof r.net.USD === 'number'));
  assert.ok(rows.every((r) => r.netText.includes('₺') && r.netText.includes('$')));
});

test('رفض المبالغ والأنواع والعملات غير الصالحة', () => {
  assert.throws(
    () => acc.addEntry({ customerId: 'C-501', type: 'damage', amount: -5, currency: 'TRY' }, 'test'),
    /المبلغ/,
  );
  assert.throws(
    () => acc.addEntry({ customerId: 'C-501', type: 'مجهول', amount: 5, currency: 'TRY' }, 'test'),
    /نوع حركة/,
  );
  assert.throws(
    () => acc.addEntry({ customerId: 'C-501', type: 'damage', amount: 5, currency: 'EUR' }, 'test'),
    /عملة غير مدعومة/,
  );
});

test('عميل له رصيد بعملة وعليه مستحقات بالأخرى يُعرض بالطرفين', async () => {
  const before = await acc.statement('سامي عودة');
  // سامي عليه مستحقات بالليرة — نضيف له تأميناً بالدولار
  acc.addEntry(
    { customerId: before.customer.id, type: 'deposit', amount: 300, currency: 'USD', note: 'تأمين' },
    'test',
  );

  const stmt = await acc.statement('سامي عودة');
  assert.equal(stmt.mixed, true);
  assert.ok(stmt.toRefund.USD > 0);
  assert.ok(stmt.toCollect.TRY > 0);

  const text = acc.statementText(stmt);
  assert.match(text, /مستحق لك/);
  assert.match(text, /مستحق علينا منك/);
  assert.match(text, /صافي الفرق بعد التحويل/);
});
