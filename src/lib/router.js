import { sendJson } from './http.js';
import { log } from './log.js';

/** موجّه مسارات بسيط يدعم متغيّرات على شكل :name */
export function createRouter() {
  const routes = [];

  function add(method, pattern, handler, options = {}) {
    const names = [];
    const regexSource = pattern
      .split('/')
      .map((segment) => {
        if (segment.startsWith(':')) {
          names.push(segment.slice(1));
          return '([^/]+)';
        }
        return segment.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      })
      .join('/');
    routes.push({
      method,
      regex: new RegExp(`^${regexSource}$`),
      names,
      handler,
      public: options.public === true,
    });
  }

  return {
    get: (p, h, o) => add('GET', p, h, o),
    post: (p, h, o) => add('POST', p, h, o),
    patch: (p, h, o) => add('PATCH', p, h, o),
    delete: (p, h, o) => add('DELETE', p, h, o),

    match(method, pathname) {
      for (const route of routes) {
        if (route.method !== method) continue;
        const m = route.regex.exec(pathname);
        if (!m) continue;
        const params = {};
        route.names.forEach((name, i) => {
          params[name] = decodeURIComponent(m[i + 1]);
        });
        return { route, params };
      }
      return null;
    },

    async run(match, req, res, ctx) {
      try {
        const result = await match.route.handler({ ...ctx, params: match.params, req, res });
        if (result !== undefined && !res.headersSent) sendJson(res, 200, result);
      } catch (err) {
        const status = err.status || 500;
        if (status >= 500) log.error(`خطأ في ${req.method} ${req.url}: ${err.message}`, err.stack);
        else log.warn(`${status} في ${req.method} ${req.url}: ${err.message}`);
        if (!res.headersSent) {
          sendJson(res, status, { error: err.message, details: err.details ?? null });
        }
      }
    },
  };
}
