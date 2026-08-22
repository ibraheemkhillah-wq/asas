import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmpDb = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'callrent-pdf-')), 'test.db');
process.env.DB_PATH = tmpDb;
process.env.EGANIS_DRIVER = 'mock';
process.env.WHATSAPP_DRIVER = 'mock';
process.env.ALLOW_WRITES = 'true';
process.env.FX_MODE = 'manual';
process.env.FX_USD_TRY = '48.05';

const pdf = await import('../src/core/statement-pdf.js');
const acc = await import('../src/core/accounting.js');
const { findChrome } = await import('../src/lib/chrome.js');

test('صفحة الكشف تحتوي كل ما يحتاجه العميل', async () => {
  const stmt = await acc.statement('أحمد نصار');
  const html = pdf.statementHtml(stmt);

  assert.match(html, /كشف حساب/);
  assert.match(html, /أحمد نصار/);
  assert.match(html, /dir="rtl"/);
  // المبالغ بعملتيها وبأرقام إنجليزية (بلا حركات يدوية: 2,820 ₺ و 200 $)
  assert.match(html, /2,820 ₺/);
  assert.match(html, /200 \$/);
  assert.equal(stmt.netText, '2,820 ₺ / 200 $');
  assert.ok(!/[٠-٩]/.test(html));
  // سعر الصرف المعتمد مذكور
  assert.match(html, /سعر الصرف المعتمد/);
  assert.match(html, /48\.05/);
  // كل حركة ظاهرة
  for (const entry of stmt.entries) assert.ok(html.includes(entry.label));
});

test('كشف عميل غير موجود يرفض التوليد', async () => {
  const stmt = await acc.statement('اسم لا وجود له إطلاقاً');
  assert.equal(stmt.found, false);
  assert.throws(() => pdf.statementHtml(stmt), /لا يوجد عميل/);
});

// التوليد الفعلي يحتاج متصفّحاً على الجهاز — يُتخطّى إن لم يوجد
test('توليد ملف PDF فعلي وحفظه في مكتبة الملفات', { skip: !findChrome() }, async () => {
  const { file, buffer, statement } = await pdf.statementPdf('أحمد نصار');

  assert.equal(buffer.subarray(0, 4).toString(), '%PDF');
  assert.ok(buffer.length > 1000);
  assert.equal(file.mime, 'application/pdf');
  assert.equal(file.kind, 'statement');
  assert.equal(file.ref, statement.customer.id);
  assert.match(file.name, /\.pdf$/);
  assert.ok(fs.existsSync(file.path));
});
