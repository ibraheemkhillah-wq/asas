import { readJson, HttpError } from '../lib/http.js';
import { config } from '../config.js';
import { eganis } from '../connectors/eganis/index.js';
import { whatsapp } from '../connectors/whatsapp/index.js';
import { recentAudit } from '../core/audit.js';
import * as inbox from '../core/inbox.js';

export function registerSystemRoutes(router) {
  router.get('/api/health', () => ({ ok: true, service: 'callrent-ops' }), { public: true });

  router.get('/api/system/status', async () => ({
    app: {
      allowWrites: config.allowWrites,
      timezone: config.timezone,
      autoSend: config.whatsapp.autoSend,
      aiConfigured: Boolean(config.ai.apiKey),
      aiModel: config.ai.model,
    },
    connectors: {
      eganis: await eganis().health(),
      whatsapp: await whatsapp().health(),
    },
  }));

  /**
   * لقطة لما يراه الخادم في لوحة eganis — تشخيص الربط من الجوال:
   *   /api/eganis/screenshot            الصفحة الرئيسية
   *   /api/eganis/screenshot?page=contracts   صفحة العقود
   */
  router.get('/api/eganis/screenshot', async ({ query, res }) => {
    const driver = eganis();
    if (typeof driver.screenshot !== 'function') {
      throw new HttpError(501, `التشخيص بالصورة متاح في وضع المتصفّح فقط (الحالي: ${driver.name})`);
    }
    const shot = await driver.screenshot(query.get('page') || '');
    res.writeHead(200, {
      'Content-Type': 'image/png',
      'Content-Length': shot.image.length,
      'Cache-Control': 'no-store',
      // العنوان وحالة الدخول في الترويسة حتى تُقرأ بلا فتح الصورة
      'X-Eganis-Url': encodeURIComponent(shot.url),
      'X-Eganis-Logged-In': String(shot.loggedIn),
    });
    res.end(shot.image);
    return null;
  });

  /** إعادة اكتشاف صفحات eganis من الصفر (بعد تغيير في اللوحة) */
  router.post('/api/eganis/refresh', async () => {
    const driver = eganis();
    if (typeof driver.refresh !== 'function') {
      return { ok: true, note: `لا حاجة لإعادة الاكتشاف في وضع ${driver.name}` };
    }
    return driver.refresh();
  });

  router.get('/api/audit', ({ query }) => recentAudit(Number(query.get('limit') || 100)));

  // ===== الردود المدرَّبة =====
  router.get('/api/templates', () => inbox.listTemplates());

  router.post('/api/templates', async ({ req }) => {
    const body = await readJson(req);
    return inbox.addTemplate({
      intent: body.intent,
      sampleIn: body.sampleIn,
      reply: body.reply,
      notes: body.notes,
    });
  });

  router.patch('/api/templates/:id', async ({ params, req }) => {
    const body = await readJson(req);
    return inbox.updateTemplate(Number(params.id), body);
  });

  router.delete('/api/templates/:id', ({ params }) => inbox.deleteTemplate(Number(params.id)));
}
