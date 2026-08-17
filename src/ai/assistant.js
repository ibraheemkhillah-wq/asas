/**
 * المساعد داخل التطبيق — محادثة مباشرة بينك وبين Claude.
 *
 * يستطيع قراءة كل ما في eganis (عقود، مركبات، عملاء، حسابات، مستندات وصور)
 * وتنفيذ الأوامر التشغيلية، وإرسال الملفات إليك داخل المحادثة.
 */
import Anthropic from '@anthropic-ai/sdk';
import { config } from '../config.js';
import { HttpError } from '../lib/http.js';
import { log } from '../lib/log.js';
import { all, run } from '../db.js';
import { eganis } from '../connectors/eganis/index.js';
import * as ops from '../core/ops.js';
import * as accounting from '../core/accounting.js';
import * as fx from '../core/fx.js';
import * as files from '../core/files.js';

let client = null;

/** حقن عميل بديل — للاختبارات فقط */
export function __setClient(replacement) {
  client = replacement;
}

function anthropic() {
  if (client) return client;
  if (!config.ai.apiKey) {
    throw new HttpError(503, 'ANTHROPIC_API_KEY غير معرّف — أضِفه في ملف .env لتفعيل المحادثة');
  }
  client = new Anthropic({ apiKey: config.ai.apiKey });
  return client;
}

const str = (description) => ({ type: 'string', description });
const num = (description) => ({ type: 'number', description });

/**
 * الأدوات المتاحة للمساعد. كلها تقرأ من eganis عبر الموصل،
 * والأوامر منها تُسجَّل في سجل التدقيق تلقائياً.
 */
export function buildTools(session) {
  return [
    {
      name: 'ops_overview',
      description: 'لوحة اليوم: المتأخرات، الإرجاعات، التسليمات، المهام، حالة الأسطول.',
      input_schema: { type: 'object', properties: {} },
      run: () => ops.overview(),
    },
    {
      name: 'list_contracts',
      description: 'عرض العقود من eganis مع تصفية بالحالة أو التاريخ أو بحث نصي.',
      input_schema: {
        type: 'object',
        properties: { status: str('open | overdue | closed'), date: str('YYYY-MM-DD'), q: str('بحث') },
      },
      run: (a) => ops.listContracts(a),
    },
    {
      name: 'get_contract',
      description: 'تفاصيل عقد محدّد برقمه.',
      input_schema: { type: 'object', properties: { id: str('رقم العقد') }, required: ['id'] },
      run: (a) => ops.getContract(a.id),
    },
    {
      name: 'list_vehicles',
      description: 'المركبات وحالتها من eganis.',
      input_schema: {
        type: 'object',
        properties: { status: str('available | rented | maintenance'), branch: str('الفرع'), q: str('بحث') },
      },
      run: (a) => ops.listVehicles(a),
    },
    {
      name: 'list_bookings',
      description: 'الحجوزات القادمة.',
      input_schema: { type: 'object', properties: { date: str('YYYY-MM-DD'), status: str('الحالة') } },
      run: (a) => ops.listBookings(a),
    },
    {
      name: 'list_tasks',
      description: 'مهام التسليم والاستلام والصيانة.',
      input_schema: { type: 'object', properties: { date: str('YYYY-MM-DD'), type: str('النوع') } },
      run: (a) => ops.listTasks(a),
    },
    {
      name: 'search_customers',
      description: 'البحث عن عميل بالاسم أو الهاتف أو رقم الهوية.',
      input_schema: { type: 'object', properties: { q: str('نص البحث') }, required: ['q'] },
      run: (a) => ops.searchCustomers(a.q),
    },
    {
      name: 'customer_statement',
      description: 'كشف حساب العميل: التأمينات والمستحقات والرصيد النهائي — كم له أو كم عليه.',
      input_schema: { type: 'object', properties: { q: str('اسم العميل أو هاتفه') }, required: ['q'] },
      run: async (a) => {
        const stmt = await accounting.statement(a.q);
        return { ...stmt, text: accounting.statementText(stmt) };
      },
    },
    {
      name: 'open_balances',
      description: 'كل العملاء الذين لهم رصيد أو عليهم مستحقات.',
      input_schema: { type: 'object', properties: {} },
      run: () => accounting.openBalances(),
    },
    {
      name: 'add_ledger_entry',
      description:
        'تسجيل حركة مالية على حساب عميل (deposit, payment, discount, deposit_refund, rent_charge, damage, fine, fuel, extra).',
      input_schema: {
        type: 'object',
        properties: {
          customerId: str('معرّف العميل'),
          customerName: str('اسمه'),
          type: str('نوع الحركة'),
          amount: num('المبلغ'),
          currency: str('عملة الحركة: TRY أو USD — سجّلها بالعملة التي حدثت بها فعلاً'),
          ref: str('المرجع'),
          note: str('الوصف'),
        },
        required: ['customerId', 'type', 'amount', 'currency'],
      },
      run: (a) => accounting.addEntry(a, 'assistant'),
    },
    {
      name: 'fx_rate',
      description:
        'سعر صرف الدولار مقابل الليرة التركية الآن (البنك المركزي التركي ثم مصادر احتياطية). استخدمه عند الحاجة لعرض مبلغ بالعملتين.',
      input_schema: {
        type: 'object',
        properties: { force: { type: 'boolean', description: 'تجاهل السعر المخزّن وجلب سعر جديد' } },
      },
      run: (a) => fx.getRate({ force: a.force === true }),
    },
    {
      name: 'list_documents',
      description:
        'المستندات والصور المرفوعة على eganis: عقود، بوالص تأمين، صور مركبات، هويات. صفِّ بالعميل أو رقم العقد أو لوحة المركبة أو النوع.',
      input_schema: {
        type: 'object',
        properties: {
          customerId: str('معرّف العميل'),
          contractNo: str('رقم العقد'),
          plate: str('رقم اللوحة'),
          type: str('contract | insurance | vehicle_photo | id'),
        },
      },
      run: async (a) => {
        const driver = eganis();
        if (typeof driver.listDocuments !== 'function') {
          throw new HttpError(501, 'المستندات غير مدعومة في وضع الربط الحالي');
        }
        return driver.listDocuments(a);
      },
    },
    {
      name: 'send_files',
      description:
        'إرسال ملفات إلى المستخدم داخل المحادثة. مرّر معرّفات المستندات من list_documents. استخدمه عندما يطلب عقداً أو تأميناً أو صوراً.',
      input_schema: {
        type: 'object',
        properties: {
          documentIds: { type: 'array', items: { type: 'string' }, description: 'معرّفات المستندات' },
        },
        required: ['documentIds'],
      },
      run: async (a) => {
        const driver = eganis();
        if (typeof driver.downloadDocument !== 'function') {
          throw new HttpError(501, 'تنزيل المستندات غير مدعوم في وضع الربط الحالي');
        }
        const sent = [];
        for (const id of a.documentIds.slice(0, 10)) {
          const doc = await driver.downloadDocument(id);
          const saved = files.saveBuffer({
            name: doc.name,
            mime: doc.mime,
            buffer: doc.buffer,
            source: 'eganis',
            ref: doc.meta?.ref || id,
            kind: doc.meta?.kind || 'other',
          });
          const described = files.describe(saved);
          session.attachments.push(described);
          sent.push({ id: described.id, name: described.name });
        }
        return { sent, note: 'وصلت الملفات للمستخدم داخل المحادثة' };
      },
    },
    {
      name: 'extend_contract',
      description: 'تمديد عقد عدداً من الأيام (أمر تعديل — يُسجَّل في سجل التدقيق).',
      input_schema: {
        type: 'object',
        properties: { id: str('رقم العقد'), days: num('عدد الأيام') },
        required: ['id', 'days'],
      },
      run: (a) => ops.extendContract(a.id, a.days, 'assistant'),
    },
    {
      name: 'close_contract',
      description: 'إغلاق عقد بعد استلام المركبة.',
      input_schema: {
        type: 'object',
        properties: { id: str('رقم العقد'), odometer: num('العدّاد'), notes: str('ملاحظات') },
        required: ['id'],
      },
      run: (a) => ops.closeContract(a.id, { odometer: a.odometer, notes: a.notes }, 'assistant'),
    },
    {
      name: 'set_vehicle_status',
      description: 'تغيير حالة مركبة: available | rented | maintenance | out_of_service.',
      input_schema: {
        type: 'object',
        properties: { id: str('اللوحة أو المعرّف'), status: str('الحالة'), note: str('السبب') },
        required: ['id', 'status'],
      },
      run: (a) => ops.setVehicleStatus(a.id, a.status, a.note, 'assistant'),
    },
  ];
}

const SYSTEM_PROMPT = `أنت مساعد التشغيل في شركة CALL & RENT لتأجير السيارات في إسطنبول، تتحدث مع صاحب الشركة داخل تطبيقه.

## مصدر البيانات
كل بيانات العملاء والعقود والمركبات والحركات المالية والمستندات مصدرها نظام eganis عبر الأدوات المتاحة لك.
لا تخترع أرقاماً أو أسماء أو تواريخ — إن لم تجدها بالأدوات، قل ذلك بوضوح.

## أسلوب الرد
- عربية واضحة ومختصرة، بلا مقدمات ولا شرح لعملك.
- ابدأ بالجواب المباشر ثم التفاصيل. الأرقام في جدول أو نقاط قصيرة عند تعدّدها.
- عند طلب مستند أو صورة: ابحث بـ list_documents ثم أرسِل الملفات فعلياً بـ send_files، ولا تكتفِ بذكر وجودها.
- عند سؤال عن حساب عميل: استخدم customer_statement واذكر الرقم النهائي أولاً (كم له أو كم عليه).

## العملات
الشركة تتعامل بالليرة التركية والدولار معاً، وبعض العملاء لهم أرصدة بالعملتين في آن واحد.
- كل مبلغ يبقى بعملته الأصلية في الدفتر؛ لا تحوّل عند التسجيل.
- عند عرض أي حساب اذكره بالعملتين بالصيغة «2,350 ₺ / 50 $»، ثم المكافئ الإجمالي إن لزم.
- اذكر سعر الصرف المعتمد ووقته ومصدره كلما عرضت مبلغاً محوَّلاً (fx_rate، وهو موجود أصلاً في نتيجة customer_statement).
- عند تسجيل حركة مالية حدّد العملة صراحة؛ إن لم تكن واضحة من كلام المستخدم فاسأله قبل التسجيل.

## الأوامر التي تغيّر البيانات
تمديد عقد، إغلاق عقد، تغيير حالة مركبة، وتسجيل حركة مالية: نفّذها فقط عندما يطلبها صراحة.
إن كان الطلب غامضاً أو المبلغ غير واضح، اسأل سؤالاً واحداً محدّداً قبل التنفيذ.
كل أمر يُسجَّل في سجل التدقيق باسمك.

## الملفات
ما يرسله لك المستخدم من صور و PDF تراه وتحلّله. الفيديو والصوت والملفات الأخرى تُحفظ لكنك لا تستطيع فتح محتواها — اذكر ذلك بصراحة عند الحاجة.`;

/** بناء سجل المحادثة السابق من قاعدة البيانات */
function history(limit = 24) {
  const rows = all(
    'SELECT role, body FROM assistant_messages ORDER BY id DESC LIMIT ?',
    [limit],
  ).reverse();
  return rows
    .filter((r) => r.body && r.body.trim())
    .map((r) => ({ role: r.role === 'assistant' ? 'assistant' : 'user', content: r.body }));
}

/** تحويل الملفات المرفوعة إلى كتل محتوى يقرأها النموذج */
function attachmentBlocks(fileIds = []) {
  const blocks = [];
  const notes = [];
  for (const id of fileIds) {
    const row = files.readFile(id);
    if (files.VIEWABLE_IMAGE.includes(row.mime)) {
      blocks.push({
        type: 'image',
        source: { type: 'base64', media_type: row.mime, data: row.buffer.toString('base64') },
      });
    } else if (files.VIEWABLE_DOC.includes(row.mime)) {
      blocks.push({
        type: 'document',
        source: { type: 'base64', media_type: 'application/pdf', data: row.buffer.toString('base64') },
        title: row.name,
      });
    } else {
      notes.push(`${row.name} (${row.mime}, ${Math.round(row.size / 1024)} كيلوبايت) — محفوظ ولا يمكن قراءة محتواه`);
    }
  }
  return { blocks, notes };
}

export function listMessages(limit = 100) {
  return all('SELECT * FROM assistant_messages ORDER BY id DESC LIMIT ?', [limit])
    .reverse()
    .map((r) => ({
      ...r,
      attachments: r.attachments ? JSON.parse(r.attachments) : [],
      tools_used: r.tools_used ? JSON.parse(r.tools_used) : [],
    }));
}

function saveMessage({ role, body, attachments = [], toolsUsed = [] }) {
  run(
    'INSERT INTO assistant_messages (role, body, attachments, tools_used) VALUES (?, ?, ?, ?)',
    [role, body || '', JSON.stringify(attachments), JSON.stringify(toolsUsed)],
  );
}

export function clearMessages() {
  run('DELETE FROM assistant_messages');
  return { ok: true };
}

/**
 * إرسال رسالة للمساعد والحصول على رده.
 * @param {{text?:string, fileIds?:string[]}} input
 */
export async function ask({ text = '', fileIds = [] } = {}) {
  if (!text.trim() && !fileIds.length) throw new HttpError(400, 'اكتب رسالة أو أرفِق ملفاً');

  const uploaded = fileIds.map((id) => files.describe(files.getFile(id)));
  saveMessage({ role: 'user', body: text, attachments: uploaded });

  const session = { attachments: [] };
  const tools = buildTools(session);
  const toolByName = new Map(tools.map((t) => [t.name, t]));
  const toolsUsed = [];

  const { blocks, notes } = attachmentBlocks(fileIds);
  const userContent = [...blocks];
  const textParts = [text.trim()];
  if (notes.length) textParts.push(`\n[ملفات مرفقة غير قابلة للقراءة: ${notes.join(' · ')}]`);
  userContent.push({ type: 'text', text: textParts.filter(Boolean).join('\n') || 'انظر المرفقات' });

  const messages = [...history(), { role: 'user', content: userContent }];

  const apiTools = tools.map(({ name, description, input_schema }) => ({
    name,
    description,
    input_schema,
  }));

  let reply = '';
  try {
    reply = await runTurns({ messages, apiTools, toolByName, toolsUsed });
  } catch (err) {
    // نحفظ الخطأ في المحادثة حتى يبقى السجل مفهوماً عند إعادة الفتح
    saveMessage({ role: 'assistant', body: `تعذّر التنفيذ: ${err.message}` });
    throw err;
  }

  if (!reply) reply = 'تم التنفيذ.';
  saveMessage({ role: 'assistant', body: reply, attachments: session.attachments, toolsUsed });

  return {
    reply,
    attachments: session.attachments,
    toolsUsed: [...new Set(toolsUsed)],
  };
}

/** حلقة الحوار مع النموذج: نصّ ← استدعاء أدوات ← نتائج ← ردّ نهائي */
async function runTurns({ messages, apiTools, toolByName, toolsUsed }) {
  let reply = '';
  for (let turn = 0; turn < 8; turn += 1) {
    const response = await anthropic().messages.create({
      model: config.ai.model,
      max_tokens: 16000,
      system: [{ type: 'text', text: SYSTEM_PROMPT, cache_control: { type: 'ephemeral' } }],
      tools: apiTools,
      messages,
    });

    if (response.stop_reason === 'refusal') {
      reply = 'تعذّر إكمال هذا الطلب. جرّب صياغته بشكل آخر أو نفّذه يدوياً من التبويبات.';
      break;
    }

    const textBlocks = response.content.filter((b) => b.type === 'text');
    if (textBlocks.length) reply = textBlocks.map((b) => b.text).join('\n').trim();

    const calls = response.content.filter((b) => b.type === 'tool_use');
    if (!calls.length) break;

    messages.push({ role: 'assistant', content: response.content });

    const results = [];
    for (const call of calls) {
      const tool = toolByName.get(call.name);
      toolsUsed.push(call.name);
      try {
        if (!tool) throw new HttpError(400, `أداة غير معروفة: ${call.name}`);
        const output = await tool.run(call.input || {});
        results.push({
          type: 'tool_result',
          tool_use_id: call.id,
          content: JSON.stringify(output ?? { ok: true }).slice(0, 60000),
        });
      } catch (err) {
        log.warn(`فشل تنفيذ الأداة ${call.name}: ${err.message}`);
        results.push({
          type: 'tool_result',
          tool_use_id: call.id,
          content: `خطأ: ${err.message}`,
          is_error: true,
        });
      }
    }
    messages.push({ role: 'user', content: results });
  }
  return reply;
}
