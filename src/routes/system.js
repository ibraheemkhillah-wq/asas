import { readJson } from '../lib/http.js';
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
