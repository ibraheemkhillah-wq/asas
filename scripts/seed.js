/**
 * تعبئة بيانات أولية: ردود مدرَّبة نموذجية + محادثة واتساب تجريبية.
 * التشغيل: npm run seed
 */
import { db, get, run } from '../src/db.js';
import { addTemplate, recordInbound } from '../src/core/inbox.js';
import { addEntry } from '../src/core/accounting.js';

const templates = [
  {
    intent: 'استفسار عن السعر',
    sampleIn: 'كم سعر تأجير السيارة باليوم؟',
    reply:
      'أهلاً وسهلاً 🌹\nالسعر يعتمد على فئة السيارة ومدة الإيجار. تفضل زوّدني بنوع السيارة المطلوبة وتاريخ الاستلام والإرجاع لأعطيك السعر النهائي.',
    notes: 'لا تُذكر أسعار محددة قبل معرفة الفئة والمدة.',
  },
  {
    intent: 'توفر سيارة',
    sampleIn: 'في عندكم سيارة متاحة بكرة؟',
    reply:
      'أهلاً بك، تحت أمرك.\nممكن تحدد لي الفئة المطلوبة (اقتصادي / متوسط / SUV) وساعة الاستلام؟ لأتأكد من التوفر وأحجزها لك.',
    notes: null,
  },
  {
    intent: 'تمديد عقد',
    sampleIn: 'بدي أمدد يومين كمان',
    reply:
      'تمام، ما في مشكلة.\nسنمدد العقد للمدة المطلوبة ونرسل لك التفاصيل المحدّثة. يرجى تأكيد عدد الأيام الإضافية.',
    notes: 'لا يتم التمديد فعلياً إلا بعد تنفيذ الأمر في النظام.',
  },
  {
    intent: 'تأخير في الإرجاع',
    sampleIn: 'رح أتأخر شوي بالتسليم',
    reply:
      'شكراً لإعلامنا مسبقاً.\nيرجى تحديد الوقت المتوقع للتسليم حتى نحدّث العقد ونتجنب أي رسوم تأخير غير ضرورية.',
    notes: null,
  },
  {
    intent: 'حادث أو عطل',
    sampleIn: 'صار معي حادث بسيط',
    reply:
      'سلامتك أولاً 🙏\nيرجى التأكد من سلامتك والتوقف بمكان آمن. سيتواصل معك المسؤول المختص فوراً لمتابعة الإجراءات.',
    notes: 'حالات الحوادث دائماً تتطلب تدخل موظف — لا يُرسل رد آلي.',
  },
  {
    intent: 'موقع المكتب',
    sampleIn: 'وين مكتبكم؟',
    reply:
      'مكتبنا الرئيسي في تقسيم، ولدينا فرع في قاضي كوي، ونوفّر التسليم في مطار صبيحة كوكجن ومطار إسطنبول.\nأخبرني بالموقع الأقرب لك وسأرسل لك العنوان ومواعيد الدوام.',
    notes: null,
  },
];

let added = 0;
for (const t of templates) {
  const exists = get('SELECT id FROM reply_templates WHERE intent = ? AND reply = ?', [
    t.intent,
    t.reply,
  ]);
  if (!exists) {
    addTemplate(t);
    added += 1;
  }
}

const demoPhone = '905321114422';
if (!get('SELECT id FROM conversations WHERE phone = ?', [demoPhone])) {
  recordInbound({
    phone: demoPhone,
    name: 'أحمد نصار',
    body: 'مرحبا، بدي أمدد العقد يومين إضافيين لو ممكن',
    waMessageId: null,
  });
  console.log('تمت إضافة محادثة تجريبية.');
}

console.log(`تم إدخال ${added} رد مدرَّب.`);

// ===== حركات محاسبية تجريبية =====
// (الحركات المشتقّة من العقود — تأمين، أجرة، دفعات — تأتي تلقائياً من eganis،
//  وهذه هي الحركات اليدوية التي يسجّلها الموظف: حوادث، مخالفات، إعادة تأمين)
const daysAgo = (n) => new Date(Date.now() - n * 86400000).toISOString();

const ledgerSeed = [
  {
    customerId: 'C-502',
    customerName: 'سامي عودة',
    phone: '905337778899',
    type: 'damage',
    amount: 4200,
    ref: 'CR-2042',
    note: 'حادث: إصلاح الصدام الأمامي والمصباح الأيسر — فاتورة الورشة 4200',
    occurredAt: daysAgo(2),
  },
  {
    customerId: 'C-501',
    customerName: 'أحمد نصار',
    phone: '905321114422',
    type: 'deposit_refund',
    amount: 2500,
    ref: 'CR-2040',
    note: 'إعادة تأمين العقد السابق نقداً',
    occurredAt: daysAgo(12),
  },
  {
    customerId: 'C-503',
    customerName: 'ليلى حجازي',
    phone: '905445556677',
    type: 'fine',
    amount: 320,
    ref: 'CR-2043',
    note: 'مخالفة سرعة — جسر الفاتح',
    occurredAt: daysAgo(1),
  },
];

let ledgerAdded = 0;
for (const entry of ledgerSeed) {
  const exists = get(
    'SELECT id FROM ledger_entries WHERE customer_id = ? AND type = ? AND amount = ?',
    [entry.customerId, entry.type, entry.amount],
  );
  if (!exists) {
    addEntry(entry, 'seed');
    ledgerAdded += 1;
  }
}
console.log(`تم إدخال ${ledgerAdded} حركة محاسبية تجريبية.`);

db.close();
