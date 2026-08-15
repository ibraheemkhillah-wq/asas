/**
 * سائق eganis عبر الـ Web Service.
 *
 * لأن كل تركيب من eganis قد يختلف في مسارات الـ API وأسماء الحقول،
 * يقرأ هذا السائق ملف تعريف JSON (config/eganis.json) يصف:
 *   - مسار تسجيل الدخول (اختياري)
 *   - مسار كل عملية (method / path / query / body)
 *   - خريطة الحقول لتحويل استجابة eganis إلى النموذج الموحّد للتطبيق
 *
 * انسخ config/eganis.example.json إلى config/eganis.json وعبّئه من توثيق حسابك.
 */
import fs from 'node:fs';
import path from 'node:path';
import { config } from '../../config.js';
import { fetchWithTimeout, HttpError } from '../../lib/http.js';
import { log } from '../../lib/log.js';

function loadProfile() {
  const file = path.resolve(process.cwd(), config.eganis.endpointsFile);
  if (!fs.existsSync(file)) {
    throw new HttpError(
      500,
      `ملف تعريف eganis غير موجود: ${file} — انسخ config/eganis.example.json وعدّله`,
    );
  }
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

/** استبدال {{name}} داخل النصوص بقيم الوسائط */
function render(template, args) {
  if (typeof template === 'string') {
    return template.replace(/\{\{(\w+)\}\}/g, (_, key) =>
      args[key] === undefined || args[key] === null ? '' : String(args[key]),
    );
  }
  if (Array.isArray(template)) return template.map((t) => render(t, args));
  if (template && typeof template === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(template)) {
      const rendered = render(v, args);
      if (rendered !== '') out[k] = rendered;
    }
    return out;
  }
  return template;
}

function pick(obj, dottedPath) {
  if (!dottedPath) return obj;
  return dottedPath.split('.').reduce((acc, key) => (acc == null ? acc : acc[key]), obj);
}

/** تحويل سجل من صيغة eganis إلى النموذج الموحّد حسب خريطة الحقول */
function mapRecord(record, fieldMap) {
  if (!fieldMap) return record;
  const out = {};
  for (const [target, source] of Object.entries(fieldMap)) {
    out[target] = typeof source === 'string' ? pick(record, source) : source;
  }
  return out;
}

export function createApiDriver() {
  const profile = loadProfile();
  const { baseUrl, username, password, apiKey, auth, apiKeyHeader, timeoutMs } = config.eganis;
  if (!baseUrl) throw new HttpError(500, 'EGANIS_BASE_URL غير معرّف');

  let sessionToken = null;
  let tokenExpiry = 0;

  async function login() {
    const spec = profile.auth;
    if (!spec || !spec.path) return null;
    const body = render(spec.body || { username: '{{username}}', password: '{{password}}' }, {
      username,
      password,
    });
    const res = await fetchWithTimeout(
      `${baseUrl}${spec.path}`,
      {
        method: spec.method || 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(body),
      },
      timeoutMs,
    );
    if (!res.ok) {
      throw new HttpError(502, `فشل تسجيل الدخول إلى eganis (${res.status})`, await res.text());
    }
    const json = await res.json();
    sessionToken = pick(json, spec.tokenPath || 'token');
    tokenExpiry = Date.now() + (spec.ttlSeconds || 1800) * 1000;
    if (!sessionToken) throw new HttpError(502, 'لم يتم استخراج رمز الجلسة من استجابة eganis');
    return sessionToken;
  }

  async function authHeaders() {
    const headers = { Accept: 'application/json' };
    if (auth === 'basic') {
      headers.Authorization = `Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`;
    } else if (auth === 'apikey') {
      headers[apiKeyHeader] = apiKey;
    } else if (auth === 'bearer') {
      if (profile.auth?.path) {
        if (!sessionToken || Date.now() > tokenExpiry) await login();
        headers.Authorization = `Bearer ${sessionToken}`;
      } else if (apiKey) {
        headers.Authorization = `Bearer ${apiKey}`;
      }
    }
    return headers;
  }

  async function call(operation, args = {}) {
    const spec = profile.endpoints?.[operation];
    if (!spec) {
      throw new HttpError(
        501,
        `العملية "${operation}" غير معرّفة في ملف eganis — أضِفها إلى endpoints`,
      );
    }
    const url = new URL(`${baseUrl}${render(spec.path, args)}`);
    for (const [key, value] of Object.entries(render(spec.query || {}, args))) {
      if (value !== '') url.searchParams.set(key, value);
    }
    const method = (spec.method || 'GET').toUpperCase();
    const headers = { ...(await authHeaders()), ...(spec.headers || {}) };
    let body;
    if (method !== 'GET' && spec.body) {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(render(spec.body, args));
    }

    log.debug(`eganis → ${method} ${url}`);
    const res = await fetchWithTimeout(url, { method, headers, body }, timeoutMs);
    const text = await res.text();
    if (!res.ok) {
      throw new HttpError(502, `استجابة خطأ من eganis (${res.status}) في ${operation}`, text.slice(0, 500));
    }
    let json;
    try {
      json = text ? JSON.parse(text) : {};
    } catch {
      throw new HttpError(502, `استجابة eganis ليست JSON في ${operation}`, text.slice(0, 300));
    }

    const data = pick(json, spec.resultPath);
    const fieldMap = spec.map ? profile.maps?.[spec.map] : null;
    if (Array.isArray(data)) return data.map((r) => mapRecord(r, fieldMap));
    if (data && typeof data === 'object') return mapRecord(data, fieldMap);
    return data;
  }

  return {
    name: 'api',
    async health() {
      try {
        await authHeaders();
        if (profile.endpoints?.health) await call('health');
        return { ok: true, driver: 'api', baseUrl };
      } catch (err) {
        return { ok: false, driver: 'api', baseUrl, error: err.message };
      }
    },
    listVehicles: (args) => call('listVehicles', args || {}),
    listContracts: (args) => call('listContracts', args || {}),
    getContract: (id) => call('getContract', { id }),
    listBookings: (args) => call('listBookings', args || {}),
    listTasks: (args) => call('listTasks', args || {}),
    searchCustomers: (q) => call('searchCustomers', { q }),
    findCustomerByPhone: async (phone) => {
      const found = await call('searchCustomers', { q: phone });
      return Array.isArray(found) ? found[0] || null : found || null;
    },
    extendContract: (id, days) => call('extendContract', { id, days }),
    closeContract: (id, opts = {}) => call('closeContract', { id, ...opts }),
    setVehicleStatus: (id, status, note) => call('setVehicleStatus', { id, status, note }),
    assignTask: (id, driver) => call('assignTask', { id, driver }),
    completeTask: (id, note) => call('completeTask', { id, note }),
    async snapshot() {
      const [vehicles, contracts, bookings, tasks] = await Promise.all([
        call('listVehicles', {}).catch(() => []),
        call('listContracts', {}).catch(() => []),
        call('listBookings', {}).catch(() => []),
        call('listTasks', {}).catch(() => []),
      ]);
      return { today: new Date().toISOString().slice(0, 10), vehicles, contracts, bookings, tasks };
    },
  };
}
