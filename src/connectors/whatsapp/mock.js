/**
 * سائق واتساب تجريبي: لا يُرسل أي رسالة فعلياً، بل يسجّلها فقط.
 * مفيد للتطوير وتدريب الردود قبل ربط الحساب الرسمي.
 */
import { log } from '../../lib/log.js';

export function createMockWhatsappDriver() {
  return {
    name: 'mock',

    async health() {
      return { ok: true, driver: 'mock', note: 'وضع المحاكاة — لا يتم إرسال رسائل فعلية' };
    },

    async sendText(to, body) {
      log.info(`whatsapp(mock) → ${to}: ${body.slice(0, 120)}`);
      return { id: `mock-${Date.now()}`, mocked: true };
    },

    async sendDocument(to, { filename, caption = '' }) {
      log.info(`whatsapp(mock) → ${to}: [مستند] ${filename}${caption ? ` — ${caption}` : ''}`);
      return { id: `mock-doc-${Date.now()}`, mocked: true };
    },

    verifySubscription() {
      return null;
    },

    verifySignature() {
      return true;
    },

    parseWebhook(payload) {
      // نقبل نفس صيغة Meta، أو صيغة مبسّطة { phone, body, name }
      if (payload?.phone && payload?.body) {
        return [
          {
            waMessageId: `mock-in-${Date.now()}`,
            phone: String(payload.phone),
            name: payload.name || null,
            body: String(payload.body),
            timestamp: new Date().toISOString(),
            type: 'text',
          },
        ];
      }
      return [];
    },
  };
}
