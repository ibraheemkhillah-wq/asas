import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmpDb = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'callrent-fx-')), 'test.db');
process.env.DB_PATH = tmpDb;
process.env.FX_MODE = 'manual';
process.env.FX_USD_TRY = '41.5';

const fx = await import('../src/core/fx.js');
const { config } = await import('../src/config.js');

test('توحيد أسماء العملات كما ترد من eganis أو من الإدخال اليدوي', () => {
  assert.equal(fx.normalizeCurrency('usd'), 'USD');
  assert.equal(fx.normalizeCurrency('$'), 'USD');
  assert.equal(fx.normalizeCurrency('دولار'), 'USD');
  assert.equal(fx.normalizeCurrency('TL'), 'TRY');
  assert.equal(fx.normalizeCurrency('₺'), 'TRY');
  assert.equal(fx.normalizeCurrency('ليرة'), 'TRY');
  // المجهول يعود للافتراضي بدل أن يكسر الحساب
  assert.equal(fx.normalizeCurrency('EUR'), 'TRY');
  assert.equal(fx.normalizeCurrency('EUR', null), null);
  assert.equal(fx.isCurrency('EUR'), false);
  assert.equal(fx.isCurrency('USD'), true);
});

test('التحويل بين العملتين بسعر محدّد', () => {
  assert.equal(fx.convert(50, 'USD', 'TRY', 40), 2000);
  assert.equal(fx.convert(2000, 'TRY', 'USD', 40), 50);
  assert.equal(fx.convert(100, 'TRY', 'TRY', 40), 100);
  assert.throws(() => fx.convert(50, 'USD', 'TRY', 0), /سعر الصرف/);
});

test('صياغة المبالغ والعرض المزدوج', () => {
  assert.match(fx.fmt(2350, 'TRY'), /₺/);
  assert.match(fx.fmt(50, 'USD'), /\$/);
  const text = fx.dual({ TRY: 2350, USD: 50 });
  assert.match(text, /₺/);
  assert.match(text, /\$/);
  assert.match(text, / \/ /);
});

test('وضع السعر اليدوي يعتمد سعر الشركة بلا شبكة', async () => {
  const rate = await fx.getRate();
  assert.equal(rate.rate, 41.5);
  assert.equal(rate.mode, 'manual');
  assert.equal(rate.stale, false);
});

test('السعر المخزَّن يُستخدم عند تعذّر المصادر', async () => {
  fx.setManualRate(43.25, 'test');

  // الانتقال إلى الوضع المباشر بلا شبكة: يجب أن يعود لآخر سعر محفوظ
  const previous = config.fx.mode;
  const previousTtl = config.fx.ttlMinutes;
  config.fx.mode = 'live';
  config.fx.ttlMinutes = 60;
  try {
    const cached = await fx.getRate();
    assert.equal(cached.rate, 43.25);
    assert.equal(cached.stale, false);
    assert.equal(cached.mode, 'live');
  } finally {
    config.fx.mode = previous;
    config.fx.ttlMinutes = previousTtl;
  }

  const history = fx.rateHistory(5);
  assert.ok(history.length >= 1);
  assert.equal(history[0].rate, 43.25);
});

test('رفض سعر صرف غير صالح', () => {
  assert.throws(() => fx.setManualRate(0, 'test'), /غير صالح/);
  assert.throws(() => fx.setManualRate('abc', 'test'), /غير صالح/);
});
