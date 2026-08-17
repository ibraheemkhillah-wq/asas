import fs from 'node:fs';
import path from 'node:path';

/** قراءة ملف .env بدون مكتبات خارجية */
function loadEnvFile(file) {
  if (!fs.existsSync(file)) return;
  const raw = fs.readFileSync(file, 'utf8');
  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    let value = trimmed.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = value;
  }
}

loadEnvFile(path.resolve(process.cwd(), '.env'));

const bool = (v, fallback = false) => {
  if (v === undefined || v === '') return fallback;
  return ['1', 'true', 'yes', 'on'].includes(String(v).toLowerCase());
};

export const config = {
  port: Number(process.env.PORT || 3000),
  host: process.env.HOST || '0.0.0.0',
  timezone: process.env.TZ || 'Asia/Hebron',
  appToken: process.env.APP_TOKEN || '',
  dbPath: process.env.DB_PATH || './data/callrent.db',
  allowWrites: bool(process.env.ALLOW_WRITES, true),

  eganis: {
    driver: process.env.EGANIS_DRIVER || 'mock',
    baseUrl: (process.env.EGANIS_BASE_URL || '').replace(/\/$/, ''),
    username: process.env.EGANIS_USERNAME || '',
    password: process.env.EGANIS_PASSWORD || '',
    apiKey: process.env.EGANIS_API_KEY || '',
    auth: process.env.EGANIS_AUTH || 'bearer',
    apiKeyHeader: process.env.EGANIS_API_KEY_HEADER || 'X-API-KEY',
    endpointsFile: process.env.EGANIS_ENDPOINTS_FILE || './config/eganis.json',
    timeoutMs: Number(process.env.EGANIS_TIMEOUT_MS || 20000),
  },

  whatsapp: {
    driver: process.env.WHATSAPP_DRIVER || 'mock',
    phoneNumberId: process.env.WA_PHONE_NUMBER_ID || '',
    token: process.env.WA_TOKEN || '',
    verifyToken: process.env.WA_VERIFY_TOKEN || 'callrent-verify',
    appSecret: process.env.WA_APP_SECRET || '',
    autoSend: bool(process.env.WA_AUTOSEND, false),
    graphVersion: process.env.WA_GRAPH_VERSION || 'v21.0',
  },

  fx: {
    // live = جلب السعر من المصادر · manual = اعتماد سعر الشركة الثابت
    mode: process.env.FX_MODE || 'live',
    manualRate: process.env.FX_USD_TRY || '',
    ttlMinutes: Number(process.env.FX_TTL_MINUTES || 15),
    // الحقل المعتمد من بيانات البنك المركزي التركي
    tcmbField: process.env.FX_TCMB_FIELD || 'ForexSelling',
  },

  ai: {
    apiKey: process.env.ANTHROPIC_API_KEY || '',
    model: process.env.ANTHROPIC_MODEL || 'claude-opus-5',
    companyProfileFile: process.env.COMPANY_PROFILE_FILE || './config/company.md',
  },
};

export function assertWritesAllowed() {
  if (!config.allowWrites) {
    const err = new Error('أوامر التعديل معطّلة (ALLOW_WRITES=false)');
    err.status = 403;
    throw err;
  }
}
