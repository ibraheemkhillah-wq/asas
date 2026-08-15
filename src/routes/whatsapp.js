import { readBody, readJson, sendJson, sendText, HttpError } from '../lib/http.js';
import { config } from '../config.js';
import { log } from '../lib/log.js';
import { whatsapp } from '../connectors/whatsapp/index.js';
import * as inbox from '../core/inbox.js';
import { draftReply } from '../ai/reply.js';

/**
 * معالجة رسالة واردة: تسجيلها ثم صياغة رد مقترح.
 * يُرسل الرد تلقائياً فقط إذا كان WA_AUTOSEND=true والثقة عالية ولا يحتاج موظفاً.
 */
async function handleInbound(message) {
  const { conversation } = inbox.recordInbound(message);
  let draft = null;
  try {
    draft = await draftReply(conversation.id);
  } catch (err) {
    log.warn(`تعذّرت صياغة رد تلقائي للمحادثة ${conversation.id}: ${err.message}`);
    return { conversationId: conversation.id, draft: null };
  }

  const autoSendable =
    config.whatsapp.autoSend && !draft.requires_human && Number(draft.confidence) >= 0.8;

  if (autoSendable) {
    await inbox.sendMessage(conversation.id, draft.reply, 'ai');
    return { conversationId: conversation.id, draft, sent: true };
  }

  inbox.saveDraft(conversation.id, draft.reply, 'ai', {
    intent: draft.intent,
    confidence: draft.confidence,
    requires_human: draft.requires_human,
    reason: draft.reason,
  });
  return { conversationId: conversation.id, draft, sent: false };
}

export function registerWhatsappRoutes(router) {
  router.get('/api/whatsapp/conversations', ({ query }) =>
    inbox.listConversations({ status: query.get('status') || undefined }),
  );

  router.get('/api/whatsapp/conversations/:id', ({ params }) => ({
    conversation: inbox.getConversation(Number(params.id)),
    messages: inbox.getMessages(Number(params.id)),
  }));

  router.post('/api/whatsapp/conversations/:id/draft', async ({ params }) => {
    const id = Number(params.id);
    const draft = await draftReply(id);
    const saved = inbox.saveDraft(id, draft.reply, 'ai', {
      intent: draft.intent,
      confidence: draft.confidence,
      requires_human: draft.requires_human,
      reason: draft.reason,
    });
    return { draft, message: saved };
  });

  router.post('/api/whatsapp/conversations/:id/send', async ({ params, req, actor }) => {
    const body = await readJson(req);
    if (!body.body || !String(body.body).trim()) throw new HttpError(400, 'نص الرسالة مطلوب');
    return inbox.sendMessage(Number(params.id), String(body.body), actor);
  });

  router.post('/api/whatsapp/conversations/:id/status', async ({ params, req }) => {
    const body = await readJson(req);
    return inbox.setConversationStatus(Number(params.id), body.status, body.assignedTo);
  });

  // ===== الويبهوك (يستدعيه واتساب — بدون رمز التطبيق) =====

  router.get(
    '/api/whatsapp/webhook',
    ({ query, res }) => {
      const challenge = whatsapp().verifySubscription(query);
      if (challenge) return sendText(res, 200, challenge);
      return sendJson(res, 403, { error: 'رمز التحقق غير صحيح' });
    },
    { public: true },
  );

  router.post(
    '/api/whatsapp/webhook',
    async ({ req, res }) => {
      const raw = await readBody(req);
      const driver = whatsapp();
      if (!driver.verifySignature(raw, req.headers['x-hub-signature-256'])) {
        return sendJson(res, 401, { error: 'توقيع غير صالح' });
      }
      let payload;
      try {
        payload = JSON.parse(raw.toString('utf8') || '{}');
      } catch {
        return sendJson(res, 400, { error: 'حمولة غير صالحة' });
      }
      // الرد على واتساب فوراً ثم المعالجة في الخلفية
      sendJson(res, 200, { received: true });
      for (const message of driver.parseWebhook(payload)) {
        handleInbound(message).catch((err) =>
          log.error(`فشل معالجة رسالة واردة: ${err.message}`),
        );
      }
      return undefined;
    },
    { public: true },
  );

  /** محاكاة رسالة واردة (للتطوير والتدريب) */
  router.post('/api/whatsapp/simulate', async ({ req }) => {
    const body = await readJson(req);
    if (!body.phone || !body.body) throw new HttpError(400, 'phone و body مطلوبان');
    return handleInbound({
      phone: body.phone,
      name: body.name || null,
      body: body.body,
      waMessageId: null,
    });
  });
}
