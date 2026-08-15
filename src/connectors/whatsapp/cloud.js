/**
 * واتساب الأعمال عبر WhatsApp Cloud API (Meta).
 * يتطلّب: WA_PHONE_NUMBER_ID، WA_TOKEN، WA_VERIFY_TOKEN، WA_APP_SECRET
 */
import crypto from 'node:crypto';
import { config } from '../../config.js';
import { fetchWithTimeout, HttpError } from '../../lib/http.js';

export function createCloudDriver() {
  const { phoneNumberId, token, verifyToken, appSecret, graphVersion } = config.whatsapp;

  return {
    name: 'cloud',

    async health() {
      if (!phoneNumberId || !token) {
        return { ok: false, driver: 'cloud', error: 'WA_PHONE_NUMBER_ID أو WA_TOKEN غير معرّف' };
      }
      try {
        const res = await fetchWithTimeout(
          `https://graph.facebook.com/${graphVersion}/${phoneNumberId}`,
          { headers: { Authorization: `Bearer ${token}` } },
          10000,
        );
        return { ok: res.ok, driver: 'cloud', status: res.status };
      } catch (err) {
        return { ok: false, driver: 'cloud', error: err.message };
      }
    },

    /** إرسال رسالة نصية */
    async sendText(to, body) {
      if (!phoneNumberId || !token) throw new HttpError(500, 'إعدادات واتساب غير مكتملة');
      const res = await fetchWithTimeout(
        `https://graph.facebook.com/${graphVersion}/${phoneNumberId}/messages`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messaging_product: 'whatsapp',
            recipient_type: 'individual',
            to: String(to).replace(/\D/g, ''),
            type: 'text',
            text: { preview_url: false, body },
          }),
        },
        20000,
      );
      const json = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new HttpError(502, `فشل إرسال رسالة واتساب (${res.status})`, json);
      }
      return { id: json.messages?.[0]?.id || null, raw: json };
    },

    /** تحقق ترويسة الاشتراك في الويبهوك (GET) */
    verifySubscription(query) {
      if (query.get('hub.mode') === 'subscribe' && query.get('hub.verify_token') === verifyToken) {
        return query.get('hub.challenge');
      }
      return null;
    },

    /** التحقق من توقيع Meta للطلب الوارد */
    verifySignature(rawBody, signatureHeader) {
      if (!appSecret) return true; // لم يُضبط سر التطبيق — تخطّي التحقق
      if (!signatureHeader) return false;
      const expected =
        'sha256=' + crypto.createHmac('sha256', appSecret).update(rawBody).digest('hex');
      const a = Buffer.from(expected);
      const b = Buffer.from(signatureHeader);
      return a.length === b.length && crypto.timingSafeEqual(a, b);
    },

    /** تحويل حمولة الويبهوك إلى رسائل موحّدة */
    parseWebhook(payload) {
      const out = [];
      for (const entry of payload.entry || []) {
        for (const change of entry.changes || []) {
          const value = change.value || {};
          const contacts = value.contacts || [];
          for (const message of value.messages || []) {
            const contact = contacts.find((c) => c.wa_id === message.from) || contacts[0];
            out.push({
              waMessageId: message.id,
              phone: message.from,
              name: contact?.profile?.name || null,
              body:
                message.text?.body ??
                message.button?.text ??
                message.interactive?.list_reply?.title ??
                `[${message.type}]`,
              timestamp: message.timestamp
                ? new Date(Number(message.timestamp) * 1000).toISOString()
                : new Date().toISOString(),
              type: message.type,
            });
          }
        }
      }
      return out;
    },
  };
}
