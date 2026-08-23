import test from 'node:test';
import assert from 'node:assert/strict';
import { arabicKeyboardToLatin, describeValue, hasArabic } from '../src/lib/keyboard.js';

test('الحروف تعود إلى مواضعها على اللوحة الإنجليزية', () => {
  assert.equal(arabicKeyboardToLatin('ضصثق'), 'qwer');
  assert.equal(arabicKeyboardToLatin('شسيب'), 'asdf');
  assert.equal(arabicKeyboardToLatin('ئءؤر'), 'zxcv');
  // كلمة حقيقية كما تخرج والكيبورد عربي
  assert.equal(arabicKeyboardToLatin('ؤشممقثىف'), 'callrent');
});

test('الأرقام العربية-الهندية تصير غربية', () => {
  assert.equal(arabicKeyboardToLatin('١٢٣٤'), '1234');
  assert.equal(arabicKeyboardToLatin('ؤشممقثىف٢٠٢٤'), 'callrent2024');
});

test('ما لا مقابل له يبقى كما هو', () => {
  assert.equal(arabicKeyboardToLatin('abc123!@#'), 'abc123!@#');
  assert.equal(arabicKeyboardToLatin(''), '');
});

test('«لا» مفتاح واحد لا حرفان', () => {
  assert.equal(arabicKeyboardToLatin('لا'), 'b');
  assert.equal(arabicKeyboardToLatin('شلاس'), 'abs');
});

test('كشف الحروف العربية', () => {
  assert.equal(hasArabic('ضصثق'), true);
  assert.equal(hasArabic('qwer123'), false);
});

test('وصف القيمة يشخّص ولا يكشف', () => {
  const pw = describeValue('ؤشممقثىف ٢٠٢٤');
  assert.deepEqual(pw.notes, ['تحوي فراغاً', 'تحوي حروفاً عربية']);
  assert.equal(pw.arabicKeyboard, true);
  // الوصف لا يحمل القيمة نفسها
  assert.equal(pw.text.includes('ؤشممقثىف'), false);

  const clean = describeValue('CallRent2024');
  assert.deepEqual(clean.notes, []);
  assert.equal(clean.text, 'سليم');
  assert.equal(clean.arabicKeyboard, false);

  assert.deepEqual(describeValue('"quoted"').notes, ['محاطة بعلامتَي اقتباس']);
});
