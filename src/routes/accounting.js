import { readJson, HttpError } from '../lib/http.js';
import * as accounting from '../core/accounting.js';
import * as inbox from '../core/inbox.js';

export function registerAccountingRoutes(router) {
  /** أنواع الحركات المتاحة — تستخدمها الواجهة لبناء القائمة */
  router.get('/api/accounting/entry-types', () =>
    Object.entries(accounting.ENTRY_TYPES).map(([type, meta]) => ({ type, ...meta })),
  );

  /** كشف حساب عميل: /api/accounting/statement?q=أحمد */
  router.get('/api/accounting/statement', async ({ query }) => {
    const stmt = await accounting.statement(query.get('q') || '');
    return { ...stmt, text: accounting.statementText(stmt) };
  });

  /** كل العملاء الذين لهم أو عليهم رصيد */
  router.get('/api/accounting/open-balances', () => accounting.openBalances());

  /** إضافة حركة يدوية */
  router.post('/api/accounting/entries', async ({ req, actor }) => {
    const body = await readJson(req);
    return accounting.addEntry(body, actor);
  });

  /** إلغاء حركة يدوية */
  router.delete('/api/accounting/entries/:id', ({ params, actor }) =>
    accounting.voidEntry(Number(params.id), actor),
  );

  /** تصفية حساب العميل بالكامل */
  router.post('/api/accounting/settle', async ({ req, actor }) => {
    const body = await readJson(req);
    if (!body.q) throw new HttpError(400, 'حدّد العميل (q)');
    return accounting.settle(body.q, { note: body.note, method: body.method }, actor);
  });

  /** إرسال كشف الحساب للعميل على واتساب (يُحفظ كمسوّدة أو يُرسل مباشرة) */
  router.post('/api/accounting/send-statement', async ({ req, actor }) => {
    const body = await readJson(req);
    const stmt = await accounting.statement(body.q || '');
    if (!stmt.found) throw new HttpError(404, stmt.message);
    const phone = stmt.customer.phone;
    if (!phone) throw new HttpError(400, 'لا يوجد رقم هاتف مسجّل لهذا العميل');

    const text = accounting.statementText(stmt);
    const conversation = inbox.upsertConversation(phone, stmt.customer.name);

    if (body.send === true) {
      await inbox.sendMessage(conversation.id, text, actor);
      return { ok: true, sent: true, conversationId: conversation.id, text };
    }
    const draft = inbox.saveDraft(conversation.id, text, actor, { kind: 'statement' });
    return { ok: true, sent: false, conversationId: conversation.id, messageId: draft.id, text };
  });
}
