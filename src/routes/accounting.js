import { readJson, HttpError } from '../lib/http.js';
import * as accounting from '../core/accounting.js';
import * as inbox from '../core/inbox.js';
import * as fx from '../core/fx.js';
import * as files from '../core/files.js';
import * as statementPdf from '../core/statement-pdf.js';

export function registerAccountingRoutes(router) {
  /** أنواع الحركات المتاحة — تستخدمها الواجهة لبناء القائمة */
  router.get('/api/accounting/entry-types', () =>
    Object.entries(accounting.ENTRY_TYPES).map(([type, meta]) => ({ type, ...meta })),
  );

  /** العملات المدعومة */
  router.get('/api/fx/currencies', () =>
    fx.CURRENCIES.map((code) => ({ code, symbol: fx.SYMBOL[code], name: fx.CURRENCY_NAME[code] })),
  );

  /** سعر صرف الدولار مقابل الليرة الآن — ?force=1 لتجاهل التخزين المؤقت */
  router.get('/api/fx/rate', ({ query }) => fx.getRate({ force: query.get('force') === '1' }));

  /** سجل الأسعار المحفوظة */
  router.get('/api/fx/history', ({ query }) => fx.rateHistory(Number(query.get('limit') || 30)));

  /** فحص كل مصادر السعر: أيها يعمل وأيها محجوب وكم يعطي — للتشخيص على الخادم */
  router.get('/api/fx/check', () => fx.checkSources());

  /** اعتماد سعر صرف من الشركة يدوياً */
  router.post('/api/fx/manual-rate', async ({ req, actor }) => {
    const body = await readJson(req);
    return fx.setManualRate(body.rate, actor);
  });

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
    return accounting.settle(
      body.q,
      { note: body.note, method: body.method, currency: body.currency, payIn: body.payIn },
      actor,
    );
  });

  /** صفحة الكشف جاهزة للطباعة — تُحفظ PDF من المتصفّح مباشرة */
  router.get('/api/accounting/statement.html', async ({ query, res }) => {
    const stmt = await accounting.statement(query.get('q') || '');
    const html = statementPdf.statementHtml(stmt);
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
    res.end(html);
    return null; // تمّ الرد يدوياً
  });

  /** كشف الحساب كملف PDF جاهز للإرسال */
  router.get('/api/accounting/statement.pdf', async ({ query, res }) => {
    const { buffer, file } = await statementPdf.statementPdf(query.get('q') || '');
    res.writeHead(200, {
      'Content-Type': 'application/pdf',
      'Content-Length': buffer.length,
      // inline = يفتح في المتصفّح · attachment = ينزل مباشرة
      'Content-Disposition': `${query.get('download') === '1' ? 'attachment' : 'inline'}; filename*=UTF-8''${encodeURIComponent(file.name)}`,
      'Cache-Control': 'no-store',
    });
    res.end(buffer);
    return null;
  });

  /**
   * إرسال كشف الحساب للعميل على واتساب.
   * as=pdf يرسله ملفاً، والافتراضي نص. send=true يرسل فعلياً، وإلا يُحفظ كمسوّدة.
   */
  router.post('/api/accounting/send-statement', async ({ req, actor }) => {
    const body = await readJson(req);
    const stmt = await accounting.statement(body.q || '');
    if (!stmt.found) throw new HttpError(404, stmt.message);
    const phone = stmt.customer.phone;
    if (!phone) throw new HttpError(400, 'لا يوجد رقم هاتف مسجّل لهذا العميل');

    const text = accounting.statementText(stmt);
    const conversation = inbox.upsertConversation(phone, stmt.customer.name);

    if (body.as === 'pdf') {
      const { file } = await statementPdf.statementPdf(body.q);
      const caption =
        body.caption ?? `كشف حسابك لدى CALL & RENT حتى ${String(stmt.generatedAt).slice(0, 10)}`;

      if (body.send === true) {
        const sent = await inbox.sendDocument(conversation.id, file, caption, actor);
        return { ok: true, sent: true, as: 'pdf', conversationId: conversation.id, file: files.describe(file), ...sent };
      }
      const draft = inbox.saveDraft(conversation.id, `${caption}\n📎 ${file.name}`, actor, {
        kind: 'statement_pdf',
        fileId: file.id,
      });
      return {
        ok: true,
        sent: false,
        as: 'pdf',
        conversationId: conversation.id,
        messageId: draft.id,
        file: files.describe(file),
      };
    }

    if (body.send === true) {
      await inbox.sendMessage(conversation.id, text, actor);
      return { ok: true, sent: true, as: 'text', conversationId: conversation.id, text };
    }
    const draft = inbox.saveDraft(conversation.id, text, actor, { kind: 'statement' });
    return { ok: true, sent: false, as: 'text', conversationId: conversation.id, messageId: draft.id, text };
  });
}
