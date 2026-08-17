import { readJson, HttpError } from '../lib/http.js';
import * as assistant from '../ai/assistant.js';
import * as files from '../core/files.js';
import { config } from '../config.js';

export function registerAssistantRoutes(router) {
  /** سجل المحادثة */
  router.get('/api/assistant/messages', () => ({
    messages: assistant.listMessages(),
    ready: Boolean(config.ai.apiKey),
    model: config.ai.model,
  }));

  /** إرسال رسالة (مع ملفات مرفوعة مسبقاً) */
  router.post('/api/assistant/message', async ({ req }) => {
    const body = await readJson(req);
    return assistant.ask({ text: body.text || '', fileIds: body.fileIds || [] });
  });

  /** مسح المحادثة */
  router.delete('/api/assistant/messages', () => assistant.clearMessages());

  /** رفع ملف (base64 من المتصفح — يدعم كل الصيغ) */
  router.post('/api/assistant/upload', async ({ req }) => {
    const body = await readJson(req, { limitBytes: 40 * 1024 * 1024 });
    if (!body.name || !body.dataBase64) throw new HttpError(400, 'اسم الملف ومحتواه مطلوبان');
    const saved = files.saveBase64({
      name: body.name,
      mime: body.mime || 'application/octet-stream',
      dataBase64: body.dataBase64,
      source: 'upload',
    });
    return files.describe(saved);
  });

  /** تنزيل/عرض ملف */
  router.get('/api/files/:id', ({ params, res, query }) => {
    const file = files.readFile(params.id);
    const disposition = query.get('download') ? 'attachment' : 'inline';
    res.writeHead(200, {
      'Content-Type': file.mime,
      'Content-Length': file.buffer.length,
      'Content-Disposition': `${disposition}; filename*=UTF-8''${encodeURIComponent(file.name)}`,
      'Cache-Control': 'private, max-age=3600',
    });
    res.end(file.buffer);
    return undefined;
  });

  /** قائمة الملفات الأخيرة */
  router.get('/api/files', ({ query }) => files.listFiles({ limit: Number(query.get('limit') || 50) }));

  /** مستندات eganis (عقود، تأمينات، صور) */
  router.get('/api/documents', async ({ query }) => {
    const { eganis } = await import('../connectors/eganis/index.js');
    const driver = eganis();
    if (typeof driver.listDocuments !== 'function') return [];
    return driver.listDocuments({
      customerId: query.get('customerId') || undefined,
      contractNo: query.get('contractNo') || undefined,
      plate: query.get('plate') || undefined,
      type: query.get('type') || undefined,
    });
  });
}
