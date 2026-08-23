import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { config } from './config.js';
import { log } from './lib/log.js';
import { sendJson, sendText } from './lib/http.js';
import { createRouter } from './lib/router.js';
import { registerOpsRoutes } from './routes/ops.js';
import { registerWhatsappRoutes } from './routes/whatsapp.js';
import { registerSystemRoutes } from './routes/system.js';
import { registerAccountingRoutes } from './routes/accounting.js';
import { registerAssistantRoutes } from './routes/assistant.js';
import * as fx from './core/fx.js';
import { applyStoredSettings } from './core/settings.js';

const router = createRouter();
registerSystemRoutes(router);
registerOpsRoutes(router);
registerWhatsappRoutes(router);
registerAccountingRoutes(router);
registerAssistantRoutes(router);

const publicDir = path.resolve(process.cwd(), 'public');
const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

function serveStatic(req, res, pathname) {
  const rel = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  const file = path.join(publicDir, rel);
  if (!file.startsWith(publicDir) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    return sendText(res, 404, 'غير موجود');
  }
  res.writeHead(200, { 'Content-Type': mimeTypes[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
  return undefined;
}

function authorize(req, query) {
  if (!config.appToken) return true; // بدون رمز — للتطوير المحلي فقط
  const header = req.headers.authorization || '';
  const bearer = header.startsWith('Bearer ') ? header.slice(7) : null;
  const token = bearer || query.get('token') || req.headers['x-app-token'];
  return token === config.appToken;
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const { pathname, searchParams: query } = url;

  if (!pathname.startsWith('/api/')) return serveStatic(req, res, pathname);

  const match = router.match(req.method, pathname);
  if (!match) return sendJson(res, 404, { error: `مسار غير معروف: ${req.method} ${pathname}` });

  if (!match.route.public && !authorize(req, query)) {
    return sendJson(res, 401, { error: 'رمز الدخول مفقود أو غير صحيح' });
  }

  const actor = ['dashboard', 'mcp', 'api'].includes(req.headers['x-actor'])
    ? req.headers['x-actor']
    : 'dashboard';
  return router.run(match, req, res, { query, actor });
});

// إعدادات محفوظة من داخل التطبيق تتقدّم على متغيّرات البيئة
applyStoredSettings();

server.listen(config.port, config.host, () => {
  log.info(`Call & Rent Ops يعمل على http://${config.host}:${config.port}`);
  log.info(`eganis=${config.eganis.driver} · whatsapp=${config.whatsapp.driver} · writes=${config.allowWrites}`);
  if (!config.appToken) log.warn('APP_TOKEN غير معرّف — الواجهة مفتوحة بدون حماية!');

  // سعر الصرف: جلب أول سعر فوراً ثم تحديث دوري في الخلفية
  if (config.fx.mode === 'manual') {
    log.info(`سعر الصرف: يدوي (${config.fx.manualRate || 'غير مضبوط'})`);
  } else {
    log.info(`سعر الصرف: ${config.fx.source} · تحديث كل ${config.fx.ttlMinutes} دقيقة`);
    fx.startAutoRefresh();
  }
});

const shutdown = () => {
  log.info('إيقاف الخادم…');
  fx.stopAutoRefresh();
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 3000).unref();
};
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
