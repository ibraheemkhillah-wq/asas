/**
 * صياغة ردود واتساب بأسلوب الشركة اعتماداً على:
 *   - ملف نبرة/سياسات الشركة (config/company.md)
 *   - الردود المدرَّبة المحفوظة في قاعدة البيانات (أمثلة بشرية)
 *   - سياق العميل من eganis (عقوده، رصيده، مواعيده)
 *   - آخر رسائل المحادثة
 */
import fs from 'node:fs';
import path from 'node:path';
import Anthropic from '@anthropic-ai/sdk';
import { config } from '../config.js';
import { HttpError } from '../lib/http.js';
import { log } from '../lib/log.js';
import { getConversation, getMessages, listTemplates, markTemplateUsed } from '../core/inbox.js';
import { customerContext } from '../core/ops.js';

let client = null;
function anthropic() {
  if (!config.ai.apiKey) {
    throw new HttpError(
      503,
      'ANTHROPIC_API_KEY غير معرّف — لا يمكن صياغة الردود تلقائياً (يمكنك الرد يدوياً)',
    );
  }
  if (!client) client = new Anthropic({ apiKey: config.ai.apiKey });
  return client;
}

function companyProfile() {
  const file = path.resolve(process.cwd(), config.ai.companyProfileFile);
  if (fs.existsSync(file)) return fs.readFileSync(file, 'utf8');
  return `اسم الشركة: Call & Rent لتأجير السيارات.
الأسلوب: عربي واضح ومهذّب، جمل قصيرة، بلا مبالغة، بلا وعود غير مؤكدة.
لا تُعطِ سعراً أو خصماً غير موجود في البيانات. عند عدم التأكد، اطلب التحويل إلى موظف.`;
}

const REPLY_SCHEMA = {
  type: 'object',
  properties: {
    reply: { type: 'string', description: 'نص الرد المقترح بالعربية، جاهز للإرسال كما هو' },
    intent: { type: 'string', description: 'سبب تواصل العميل بكلمات قليلة' },
    confidence: { type: 'number', description: 'درجة الثقة بين 0 و 1' },
    requires_human: { type: 'boolean', description: 'هل يحتاج الرد لمراجعة/تدخل موظف' },
    reason: { type: 'string', description: 'سبب مختصر للتقييم أو ما ينقص من معلومات' },
  },
  required: ['reply', 'intent', 'confidence', 'requires_human', 'reason'],
  additionalProperties: false,
};

function buildSystemPrompt(templates) {
  const examples = templates
    .slice(0, 40)
    .map(
      (t, i) =>
        `مثال ${i + 1} — الموضوع: ${t.intent}\n` +
        (t.sample_in ? `رسالة العميل: ${t.sample_in}\n` : '') +
        `الرد المعتمد: ${t.reply}` +
        (t.notes ? `\nملاحظة: ${t.notes}` : ''),
    )
    .join('\n\n');

  return `أنت موظف خدمة عملاء في شركة تأجير سيارات، تكتب ردود واتساب باللغة العربية.

## هوية الشركة وأسلوبها
${companyProfile()}

## قواعد ثابتة
- اكتب رداً واحداً جاهزاً للإرسال، بلا مقدمات ولا شرح لعملك.
- استخدم فقط المعلومات الموجودة في سياق العميل أدناه. لا تخترع أسعاراً أو مواعيد أو أرقام عقود.
- إذا كانت المعلومة ناقصة أو الطلب حسّاس (حادث، مخالفة، نزاع مالي، إلغاء بغرامة)، اجعل requires_human = true واكتب رداً يطمئن العميل ويخبره أن الموظف المختص سيتابع معه.
- حافظ على نبرة الأمثلة المعتمدة أدناه: نفس مستوى الرسمية وطول الجملة وطريقة التحية.
- لا تكرر تحية طويلة في منتصف محادثة جارية.

${examples ? `## ردود معتمدة سابقاً (اتبع أسلوبها)\n${examples}` : '## لا توجد ردود مدرَّبة بعد — استخدم أسلوباً مهنياً مختصراً.'}`;
}

function buildUserPrompt({ conversation, messages, context }) {
  const history = messages
    .slice(-12)
    .map((m) => `${m.direction === 'in' ? 'العميل' : 'الشركة'}: ${m.body}`)
    .join('\n');

  const customer = context.customer
    ? `الاسم: ${context.customer.name} | الهاتف: ${context.customer.phone}${
        context.customer.blacklisted ? ' | ⚠️ مدرج في القائمة السوداء' : ''
      }`
    : 'عميل غير مسجّل في النظام.';

  const contracts = (context.contracts || [])
    .slice(0, 5)
    .map(
      (c) =>
        `عقد ${c.no} | مركبة ${c.plate} | من ${String(c.startAt).slice(0, 10)} إلى ${String(
          c.endAt,
        ).slice(0, 10)} | الحالة ${c.status} | الرصيد ${c.balance}`,
    )
    .join('\n');

  return `## سياق العميل
${customer}
${contracts ? `\n### عقوده\n${contracts}` : '\nلا توجد عقود مرتبطة بهذا الرقم.'}

## المحادثة (الأحدث في الأسفل)
${history}

اكتب الرد المناسب على آخر رسالة من العميل.`;
}

/**
 * صياغة رد مقترح لمحادثة.
 * @param {number} conversationId
 * @returns {Promise<{reply:string,intent:string,confidence:number,requires_human:boolean,reason:string,model:string}>}
 */
export async function draftReply(conversationId) {
  const conversation = getConversation(conversationId);
  const messages = getMessages(conversationId, 30);
  if (!messages.length) throw new HttpError(400, 'لا توجد رسائل في هذه المحادثة');

  const templates = listTemplates({ activeOnly: true });
  const context = await customerContext(conversation.phone).catch((err) => {
    log.warn(`تعذّر جلب سياق العميل من eganis: ${err.message}`);
    return { customer: null, contracts: [] };
  });

  const response = await anthropic().messages.create({
    model: config.ai.model,
    max_tokens: 2000,
    system: [
      {
        type: 'text',
        text: buildSystemPrompt(templates),
        cache_control: { type: 'ephemeral' },
      },
    ],
    output_config: { format: { type: 'json_schema', schema: REPLY_SCHEMA } },
    messages: [{ role: 'user', content: buildUserPrompt({ conversation, messages, context }) }],
  });

  if (response.stop_reason === 'refusal') {
    throw new HttpError(422, 'تعذّرت صياغة الرد تلقائياً — يرجى الرد يدوياً');
  }

  const textBlock = response.content.find((b) => b.type === 'text');
  if (!textBlock) throw new HttpError(502, 'استجابة غير متوقعة من نموذج الصياغة');

  let draft;
  try {
    draft = JSON.parse(textBlock.text);
  } catch {
    throw new HttpError(502, 'تعذّر تحليل الرد المقترح');
  }

  // تحديث عدّاد استخدام القالب الأقرب موضوعاً (تتبّع بسيط للتدريب)
  const matched = templates.find((t) => draft.intent && t.intent.includes(draft.intent.slice(0, 6)));
  if (matched) markTemplateUsed(matched.id);

  return {
    ...draft,
    model: response.model,
    usage: {
      input: response.usage?.input_tokens,
      output: response.usage?.output_tokens,
      cacheRead: response.usage?.cache_read_input_tokens,
    },
  };
}
