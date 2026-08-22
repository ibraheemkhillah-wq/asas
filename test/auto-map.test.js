import test from 'node:test';
import assert from 'node:assert/strict';
import * as map from '../src/connectors/eganis/auto-map.js';

// ترويسة عقود كما تظهر في لوحة eganis التركية
const CONTRACT_HEADERS = [
  'Sözleşme No', 'Müşteri', 'Telefon', 'Plaka', 'Başlangıç', 'Bitiş',
  'Durum', 'Günlük', 'Toplam', 'Ödenen', 'Bakiye', 'Depozito', 'Para Birimi',
];

test('تبسيط الحروف التركية للمطابقة', () => {
  assert.equal(map.normalizeHeader('Sözleşme No'), 'sozlesme no');
  assert.equal(map.normalizeHeader('Müşteri Adı'), 'musteri adi');
  assert.equal(map.normalizeHeader('Araç Durumu'), 'arac durumu');
  assert.equal(map.normalizeHeader('  Ödenen  '), 'odenen');
});

test('مطابقة أعمدة العقود بأسمائها التركية', () => {
  const columns = map.mapColumns(CONTRACT_HEADERS, 'contract');
  assert.equal(columns.no, 0);
  assert.equal(columns.customerName, 1);
  assert.equal(columns.phone, 2);
  assert.equal(columns.plate, 3);
  assert.equal(columns.startAt, 4);
  assert.equal(columns.endAt, 5);
  assert.equal(columns.status, 6);
  assert.equal(columns.total, 8);
  assert.equal(columns.paid, 9);
  assert.equal(columns.balance, 10);
  assert.equal(columns.deposit, 11);
  assert.equal(columns.currency, 12);
});

test('لا يُسنَد العمود نفسه لحقلين', () => {
  const columns = map.mapColumns(CONTRACT_HEADERS, 'contract');
  const indexes = Object.values(columns);
  assert.equal(new Set(indexes).size, indexes.length);
});

test('قراءة الأرقام التركية والإنجليزية', () => {
  assert.equal(map.parseNumber('3.000,50'), 3000.5);
  assert.equal(map.parseNumber('1,234.56'), 1234.56);
  assert.equal(map.parseNumber('480,00'), 480);
  assert.equal(map.parseNumber('120'), 120);
  assert.equal(map.parseNumber('1.500,00 ₺'), 1500);
  assert.equal(map.parseNumber(''), null);
});

test('قراءة التواريخ التركية بتوقيت الشركة لا بتوقيت غرينتش', () => {
  assert.equal(map.parseDate('18.08.2026'), '2026-08-18T00:00:00');
  assert.equal(map.parseDate('01/09/2026'), '2026-09-01T00:00:00');
  assert.equal(map.parseDate('18.08.2026 14:30'), '2026-08-18T14:30:00');
  assert.equal(map.parseDate(''), null);
  assert.equal(map.parseDate('نص ليس تاريخاً'), null);
  assert.equal(map.parseDate('45.13.2026'), null);

  // اليوم لا ينزاح مهما كان توقيت الخادم
  const d = new Date(map.parseDate('18.08.2026 09:00'));
  assert.equal(d.getDate(), 18);
  assert.equal(d.getHours(), 9);
});

test('ترجمة الحالات التركية', () => {
  assert.equal(map.contractStatus('Açık'), 'open');
  assert.equal(map.contractStatus('Kapalı'), 'closed');
  assert.equal(map.contractStatus('Gecikmiş'), 'overdue');
  assert.equal(map.vehicleStatus('Müsait'), 'available');
  assert.equal(map.vehicleStatus('Kirada'), 'rented');
  assert.equal(map.vehicleStatus('Bakımda'), 'maintenance');
  assert.equal(map.bookingStatus('Onaylı'), 'confirmed');
});

test('تمييز العملة', () => {
  assert.equal(map.parseCurrency('TL'), 'TRY');
  assert.equal(map.parseCurrency('USD'), 'USD');
  assert.equal(map.parseCurrency('$'), 'USD');
  assert.equal(map.parseCurrency('₺'), 'TRY');
  assert.equal(map.parseCurrency('EUR'), null);
});

test('تحويل صفوف العقود إلى سجلات التطبيق', () => {
  const rows = [
    ['CR-2041', 'Ahmet Nassar', '0532 111 44 22', '34 ABC 123', '18.08.2026', '22.08.2026',
      'Açık', '120,00', '480,00', '300,00', '180,00', '3.000,00', 'TL'],
    ['CR-2043', 'Leyla Hicazi', '0544 555 66 77', '34 XYZ 789', '16.08.2026', '22.08.2026',
      'Açık', '60,00', '360,00', '360,00', '0,00', '150,00', 'USD'],
  ];
  const [first, second] = map.mapRows(CONTRACT_HEADERS, rows, 'contract');

  assert.equal(first.no, 'CR-2041');
  assert.equal(first.customerName, 'Ahmet Nassar');
  assert.equal(first.plate, '34 ABC 123');
  assert.equal(first.status, 'open');
  assert.equal(first.total, 480);
  assert.equal(first.paid, 300);
  assert.equal(first.balance, 180);
  assert.equal(first.deposit, 3000);
  assert.equal(first.currency, 'TRY');
  assert.match(first.startAt, /^2026-08-18T/);

  // العقد بالدولار يصل بعملته — وهذا أساس المحاسبة بالعملتين
  assert.equal(second.currency, 'USD');
  assert.equal(second.deposit, 150);
});

test('حساب الرصيد عند غياب عموده', () => {
  const headers = ['Sözleşme No', 'Müşteri', 'Başlangıç', 'Toplam', 'Ödenen'];
  const [row] = map.mapRows(headers, [['CR-1', 'Ali', '01.08.2026', '1.000,00', '400,00']], 'contract');
  assert.equal(row.balance, 600);
});

test('حركات الحساب: عمودا مدين ودائن بدل عمود مبلغ', () => {
  const headers = ['Tarih', 'Açıklama', 'Belge No', 'Borç', 'Alacak', 'Bakiye', 'Para Birimi'];
  const rows = [
    ['18.08.2026', 'Depozito', 'CR-2041', '0,00', '3.000,00', '3.000,00', 'TL'],
    ['22.08.2026', 'Kira bedeli', 'CR-2041', '480,00', '0,00', '2.520,00', 'TL'],
  ];
  const [deposit, rent] = map.mapRows(headers, rows, 'ledgerEntry');

  assert.equal(deposit.amount, 3000);
  assert.equal(deposit.direction, 'credit');
  assert.equal(deposit.currency, 'TRY');
  assert.equal(rent.amount, 480);
  assert.equal(rent.direction, 'debit');
  assert.equal(rent.ref, 'CR-2041');
});

test('جودة المطابقة تميّز الجدول الصحيح من جدول عابر', () => {
  const good = map.mappingScore(CONTRACT_HEADERS, 'contract');
  const noise = map.mappingScore(['Sıra', 'Not', 'İşlem'], 'contract');
  assert.equal(good.score, 1);
  assert.ok(noise.score < good.score);
});

test('مطابقة الأعمدة الإنجليزية أيضاً', () => {
  const columns = map.mapColumns(
    ['Contract No', 'Customer', 'Plate', 'Start', 'End', 'Status', 'Total', 'Paid', 'Balance'],
    'contract',
  );
  assert.equal(columns.no, 0);
  assert.equal(columns.customerName, 1);
  assert.equal(columns.plate, 2);
  assert.equal(columns.balance, 8);
});
