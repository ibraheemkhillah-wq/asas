import test from 'node:test';
import assert from 'node:assert/strict';
import { panelBase } from '../src/config.js';

/*
 * صاحب الشركة ينسخ رابط اللوحة من شريط المتصفّح على جواله، فيأتي رابط صفحة
 * الدخول نفسها ومعه ReturnUrl وأحياناً فراغ أو سطر جديد لا يُرى. لو أبقيناه
 * كما هو، بُنيت روابط الصفحات الداخلية فوقه فخرجت معطوبة وفشل الاكتشاف.
 */
test('رابط صفحة الدخول يُرجَع إلى جذر اللوحة', () => {
  assert.equal(
    panelBase('https://rac.eganisyazilim.com/Account/Login'),
    'https://rac.eganisyazilim.com',
  );
  assert.equal(
    panelBase('https://rac.eganisyazilim.com/Account/Login?ReturnUrl=%2F'),
    'https://rac.eganisyazilim.com',
  );
  assert.equal(panelBase('https://x.com/Identity/Account/Login'), 'https://x.com');
  assert.equal(panelBase('https://x.com/giris'), 'https://x.com');
});

test('الفراغ والسطر الجديد من النسخ اليدوي يُقلَّمان', () => {
  assert.equal(panelBase('  https://x.com/panel  \n'), 'https://x.com/panel');
  assert.equal(panelBase('https://x.com/panel/'), 'https://x.com/panel');
});

test('مسار لوحة حقيقي لا يُقصّ', () => {
  assert.equal(panelBase('https://x.com/panel'), 'https://x.com/panel');
  assert.equal(panelBase('https://x.com/rac/Sozlesmeler'), 'https://x.com/rac/Sozlesmeler');
});

test('رابط بلا بروتوكول يُكمَّل بـ https', () => {
  assert.equal(panelBase('rac.eganisyazilim.com'), 'https://rac.eganisyazilim.com');
});

test('قيمة فارغة تبقى فارغة', () => {
  assert.equal(panelBase(''), '');
  assert.equal(panelBase(undefined), '');
});
