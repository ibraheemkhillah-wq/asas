#!/usr/bin/env node
/**
 * خادم MCP — يمنح Claude وصولاً مباشراً إلى عمليات الشركة.
 *
 * يتحدّث مع خادم التطبيق عبر HTTP (نفس المسارات ونفس التدقيق)،
 * لذا يجب أن يكون الخادم يعمل: npm start
 *
 * الإعداد في Claude Code / Claude Desktop:
 *   {
 *     "mcpServers": {
 *       "callrent": {
 *         "command": "node",
 *         "args": ["/absolute/path/asas/src/mcp/server.js"],
 *         "env": { "APP_URL": "http://127.0.0.1:3000", "APP_TOKEN": "..." }
 *       }
 *     }
 *   }
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { config } from '../config.js';

const APP_URL = (process.env.APP_URL || `http://127.0.0.1:${config.port}`).replace(/\/$/, '');
const APP_TOKEN = process.env.APP_TOKEN || config.appToken;

async function api(method, pathname, { query, body } = {}) {
  const url = new URL(APP_URL + pathname);
  for (const [key, value] of Object.entries(query || {})) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, value);
  }
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${APP_TOKEN}`,
      'X-Actor': 'mcp',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    throw new Error(data.error || `فشل الطلب (${res.status}) على ${pathname}`);
  }
  return data;
}

const str = (description) => ({ type: 'string', description });
const num = (description) => ({ type: 'number', description });

const tools = [
  {
    name: 'ops_overview',
    description:
      'لوحة تشغيل اليوم: العقود المتأخرة، الإرجاعات المستحقة اليوم، التسليمات، المهام، وحالة الأسطول والتنبيهات.',
    inputSchema: { type: 'object', properties: {} },
    run: () => api('GET', '/api/ops/overview'),
  },
  {
    name: 'list_contracts',
    description: 'عرض العقود مع تصفية اختيارية بالحالة (open/overdue/closed/reserved) أو التاريخ أو نص بحث.',
    inputSchema: {
      type: 'object',
      properties: {
        status: str('حالة العقد: open | overdue | closed | reserved'),
        date: str('تاريخ بصيغة YYYY-MM-DD'),
        q: str('بحث بالاسم أو الهاتف أو رقم اللوحة أو رقم العقد'),
      },
    },
    run: (args) => api('GET', '/api/ops/contracts', { query: args }),
  },
  {
    name: 'get_contract',
    description: 'تفاصيل عقد محدّد مع الملاحظات المرتبطة به.',
    inputSchema: {
      type: 'object',
      properties: { id: str('رقم العقد أو معرّفه') },
      required: ['id'],
    },
    run: (args) => api('GET', `/api/ops/contracts/${encodeURIComponent(args.id)}`),
  },
  {
    name: 'list_vehicles',
    description: 'عرض المركبات وحالتها (available/rented/maintenance/out_of_service).',
    inputSchema: {
      type: 'object',
      properties: { status: str('حالة المركبة'), branch: str('الفرع'), q: str('بحث') },
    },
    run: (args) => api('GET', '/api/ops/vehicles', { query: args }),
  },
  {
    name: 'list_bookings',
    description: 'عرض الحجوزات القادمة.',
    inputSchema: {
      type: 'object',
      properties: { date: str('YYYY-MM-DD'), status: str('new | confirmed | cancelled') },
    },
    run: (args) => api('GET', '/api/ops/bookings', { query: args }),
  },
  {
    name: 'list_tasks',
    description: 'مهام التسليم والاستلام والصيانة.',
    inputSchema: {
      type: 'object',
      properties: { date: str('YYYY-MM-DD'), type: str('delivery | pickup | maintenance') },
    },
    run: (args) => api('GET', '/api/ops/tasks', { query: args }),
  },
  {
    name: 'search_customers',
    description: 'البحث عن عميل بالاسم أو الهاتف أو رقم الهوية.',
    inputSchema: { type: 'object', properties: { q: str('نص البحث') }, required: ['q'] },
    run: (args) => api('GET', '/api/ops/customers', { query: args }),
  },
  {
    name: 'customer_context',
    description: 'ملف العميل حسب رقم الهاتف: بياناته وعقوده — مفيد قبل الرد على واتساب.',
    inputSchema: { type: 'object', properties: { phone: str('رقم الهاتف') }, required: ['phone'] },
    run: (args) => api('GET', '/api/ops/customer-context', { query: args }),
  },

  // ===== أوامر تعديل =====
  {
    name: 'extend_contract',
    description: 'تمديد عقد لعدد من الأيام. أمر تعديل — يُسجَّل في سجل التدقيق.',
    inputSchema: {
      type: 'object',
      properties: { id: str('رقم العقد'), days: num('عدد الأيام') },
      required: ['id', 'days'],
    },
    run: (args) =>
      api('POST', `/api/ops/contracts/${encodeURIComponent(args.id)}/extend`, {
        body: { days: args.days },
      }),
  },
  {
    name: 'close_contract',
    description: 'إغلاق عقد بعد استلام المركبة (مع قراءة العدّاد وملاحظات اختيارية).',
    inputSchema: {
      type: 'object',
      properties: {
        id: str('رقم العقد'),
        odometer: num('قراءة العدّاد عند الاستلام'),
        notes: str('ملاحظات'),
      },
      required: ['id'],
    },
    run: (args) =>
      api('POST', `/api/ops/contracts/${encodeURIComponent(args.id)}/close`, {
        body: { odometer: args.odometer, notes: args.notes },
      }),
  },
  {
    name: 'set_vehicle_status',
    description: 'تغيير حالة مركبة: available | rented | maintenance | out_of_service.',
    inputSchema: {
      type: 'object',
      properties: { id: str('معرّف المركبة أو رقم اللوحة'), status: str('الحالة'), note: str('سبب') },
      required: ['id', 'status'],
    },
    run: (args) =>
      api('POST', `/api/ops/vehicles/${encodeURIComponent(args.id)}/status`, {
        body: { status: args.status, note: args.note },
      }),
  },
  {
    name: 'assign_task',
    description: 'إسناد مهمة تسليم/استلام إلى سائق.',
    inputSchema: {
      type: 'object',
      properties: { id: str('رقم المهمة'), driver: str('اسم السائق') },
      required: ['id', 'driver'],
    },
    run: (args) =>
      api('POST', `/api/ops/tasks/${encodeURIComponent(args.id)}/assign`, {
        body: { driver: args.driver },
      }),
  },
  {
    name: 'complete_task',
    description: 'إنهاء مهمة تشغيلية.',
    inputSchema: {
      type: 'object',
      properties: { id: str('رقم المهمة'), note: str('ملاحظة') },
      required: ['id'],
    },
    run: (args) =>
      api('POST', `/api/ops/tasks/${encodeURIComponent(args.id)}/complete`, {
        body: { note: args.note },
      }),
  },
  {
    name: 'add_note',
    description: 'إضافة ملاحظة تشغيلية على عقد أو مركبة أو عميل.',
    inputSchema: {
      type: 'object',
      properties: {
        refType: str('contract | vehicle | customer | booking'),
        refId: str('المعرّف'),
        body: str('نص الملاحظة'),
      },
      required: ['refType', 'refId', 'body'],
    },
    run: (args) => api('POST', '/api/ops/notes', { body: args }),
  },

  {
    name: 'list_documents',
    description:
      'المستندات والصور المرفوعة على eganis: العقود، بوالص التأمين، صور المركبات، الهويات. صفِّ بالعميل أو رقم العقد أو اللوحة أو النوع.',
    inputSchema: {
      type: 'object',
      properties: {
        customerId: str('معرّف العميل'),
        contractNo: str('رقم العقد'),
        plate: str('رقم اللوحة'),
        type: str('contract | insurance | vehicle_photo | id'),
      },
    },
    run: (args) => api('GET', '/api/documents', { query: args }),
  },

  // ===== محاسبة المستأجرين =====
  {
    name: 'customer_statement',
    description:
      'كشف حساب عميل: كل الحركات (تأمينات، أجرة، دفعات، حوادث، مخالفات) مع الرصيد النهائي — كم له علينا أو كم عليه لنا، ونص جاهز للإرسال.',
    inputSchema: {
      type: 'object',
      properties: { q: str('اسم العميل أو رقم هاتفه أو معرّفه') },
      required: ['q'],
    },
    run: (args) => api('GET', '/api/accounting/statement', { query: args }),
  },
  {
    name: 'open_balances',
    description: 'كل العملاء الذين لهم رصيد عندنا أو عليهم مستحقات، مرتّبين بالأكبر مبلغاً.',
    inputSchema: { type: 'object', properties: {} },
    run: () => api('GET', '/api/accounting/open-balances'),
  },
  {
    name: 'add_ledger_entry',
    description:
      'إضافة حركة مالية على حساب عميل. الأنواع: deposit تأمين، payment دفعة، discount خصم (لصالح العميل) — deposit_refund إعادة تأمين، rent_charge أجرة، damage تكاليف حادث، fine مخالفة، fuel وقود، extra رسوم (على العميل).',
    inputSchema: {
      type: 'object',
      properties: {
        customerId: str('معرّف العميل من eganis'),
        customerName: str('اسم العميل'),
        phone: str('هاتف العميل'),
        type: str('نوع الحركة'),
        amount: num('المبلغ بعملته'),
        currency: str('عملة الحركة: TRY أو USD — سجّلها كما حدثت فعلاً بلا تحويل'),
        ref: str('رقم العقد أو المرجع'),
        note: str('وصف الحركة'),
      },
      required: ['customerId', 'type', 'amount', 'currency'],
    },
    run: (args) => api('POST', '/api/accounting/entries', { body: args }),
  },
  {
    name: 'settle_customer',
    description:
      'تصفية حساب عميل: تسجّل إعادة الرصيد له أو تحصيل المستحقات منه فيصبح الحساب صفراً. تُصفّى الليرة والدولار كلٌّ على حدة. استخدمه بعد تأكيد المستخدم.',
    inputSchema: {
      type: 'object',
      properties: {
        q: str('اسم العميل أو هاتفه'),
        method: str('طريقة التسوية: نقداً / حوالة / خصم'),
        currency: str('تصفية عملة واحدة فقط: TRY أو USD (الافتراضي: كل العملات)'),
        payIn: str('العملة المستلمة/المدفوعة فعلياً إن اختلفت عن عملة الرصيد'),
        note: str('ملاحظة'),
      },
      required: ['q'],
    },
    run: (args) => api('POST', '/api/accounting/settle', { body: args }),
  },
  {
    name: 'fx_rate',
    description:
      'سعر صرف الدولار مقابل الليرة التركية الآن مع مصدره ووقته (البنك المركزي التركي ثم مصادر احتياطية).',
    inputSchema: {
      type: 'object',
      properties: { force: { type: 'boolean', description: 'تجاهل السعر المخزّن وجلب سعر جديد' } },
    },
    run: (args) => api('GET', '/api/fx/rate', { query: args.force ? { force: '1' } : {} }),
  },
  {
    name: 'fx_check_sources',
    description:
      'فحص كل مصادر سعر الصرف (حرم ألتين، البنك المركزي التركي، المصادر الاحتياطية): أيها يستجيب وأيها محجوب وكم يعطي. استخدمه لتشخيص أي مشكلة في تحديث السعر.',
    inputSchema: { type: 'object', properties: {} },
    run: () => api('GET', '/api/fx/check'),
  },
  {
    name: 'fx_set_rate',
    description: 'اعتماد سعر صرف من الشركة يدوياً (كم ليرة للدولار الواحد).',
    inputSchema: {
      type: 'object',
      properties: { rate: num('كم ليرة للدولار') },
      required: ['rate'],
    },
    run: (args) => api('POST', '/api/fx/manual-rate', { body: args }),
  },
  {
    name: 'send_statement',
    description:
      'تجهيز كشف حساب العميل في محادثته على واتساب. as=pdf يرسله ملفاً بهوية الشركة، والافتراضي نص. يُحفظ كمسوّدة إلا إذا مرّرت send=true بعد موافقة المستخدم.',
    inputSchema: {
      type: 'object',
      properties: {
        q: str('اسم العميل أو هاتفه'),
        as: str('pdf لإرساله ملفاً · text لإرساله رسالة نصية (الافتراضي)'),
        caption: str('نص مرافق للملف'),
        send: { type: 'boolean', description: 'إرسال فعلي' },
      },
      required: ['q'],
    },
    run: (args) => api('POST', '/api/accounting/send-statement', { body: args }),
  },
  {
    name: 'statement_pdf',
    description:
      'توليد كشف حساب العميل كملف PDF بهوية الشركة وحفظه في مكتبة الملفات، ويعيد رابطه ليُفتح أو يُرسل.',
    inputSchema: { type: 'object', properties: { q: str('اسم العميل أو هاتفه') }, required: ['q'] },
    run: (args) =>
      api('POST', '/api/accounting/send-statement', { body: { ...args, as: 'pdf', send: false } }),
  },

  // ===== واتساب =====
  {
    name: 'whatsapp_conversations',
    description: 'قائمة محادثات واتساب مرتّبة بالأحدث.',
    inputSchema: {
      type: 'object',
      properties: { status: str('open | pending | closed') },
    },
    run: (args) => api('GET', '/api/whatsapp/conversations', { query: args }),
  },
  {
    name: 'whatsapp_conversation',
    description: 'قراءة محادثة واتساب كاملة برسائلها.',
    inputSchema: { type: 'object', properties: { id: num('رقم المحادثة') }, required: ['id'] },
    run: (args) => api('GET', `/api/whatsapp/conversations/${args.id}`),
  },
  {
    name: 'whatsapp_draft_reply',
    description:
      'صياغة رد مقترح لمحادثة بأسلوب الشركة والردود المدرَّبة (يحفظه كمسوّدة ولا يرسله).',
    inputSchema: { type: 'object', properties: { id: num('رقم المحادثة') }, required: ['id'] },
    run: (args) => api('POST', `/api/whatsapp/conversations/${args.id}/draft`),
  },
  {
    name: 'whatsapp_send',
    description:
      'إرسال رسالة واتساب فعلياً للعميل. استخدمه فقط بعد موافقة صريحة على النص من المستخدم.',
    inputSchema: {
      type: 'object',
      properties: { id: num('رقم المحادثة'), body: str('نص الرسالة') },
      required: ['id', 'body'],
    },
    run: (args) =>
      api('POST', `/api/whatsapp/conversations/${args.id}/send`, { body: { body: args.body } }),
  },
  {
    name: 'list_reply_templates',
    description: 'عرض الردود المدرَّبة المعتمدة.',
    inputSchema: { type: 'object', properties: {} },
    run: () => api('GET', '/api/templates'),
  },
  {
    name: 'add_reply_template',
    description: 'إضافة رد بشري معتمد ليتعلّم منه النظام في الردود القادمة.',
    inputSchema: {
      type: 'object',
      properties: {
        intent: str('موضوع الرسالة، مثل: استفسار سعر'),
        sampleIn: str('رسالة عميل نموذجية'),
        reply: str('نص الرد المعتمد'),
        notes: str('ملاحظات للاستخدام'),
      },
      required: ['intent', 'reply'],
    },
    run: (args) => api('POST', '/api/templates', { body: args }),
  },
  {
    name: 'system_status',
    description: 'حالة الاتصال بـ eganis وواتساب وإعدادات التطبيق.',
    inputSchema: { type: 'object', properties: {} },
    run: () => api('GET', '/api/system/status'),
  },
  {
    name: 'audit_log',
    description: 'آخر الأوامر التي نُفّذت عبر النظام ومن نفّذها.',
    inputSchema: { type: 'object', properties: { limit: num('عدد السجلات') } },
    run: (args) => api('GET', '/api/audit', { query: args }),
  },
];

const server = new Server(
  { name: 'callrent-ops', version: '0.1.0' },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: tools.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })),
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = tools.find((t) => t.name === request.params.name);
  if (!tool) {
    return { isError: true, content: [{ type: 'text', text: `أداة غير معروفة: ${request.params.name}` }] };
  }
  try {
    const result = await tool.run(request.params.arguments || {});
    return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
  } catch (err) {
    return { isError: true, content: [{ type: 'text', text: `خطأ: ${err.message}` }] };
  }
});

await server.connect(new StdioServerTransport());
