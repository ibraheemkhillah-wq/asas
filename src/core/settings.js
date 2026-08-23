/**
 * إعدادات التشغيل من داخل التطبيق.
 *
 * لماذا؟ لأن صاحب الشركة يعمل من جواله، وتعديل متغيّرات البيئة في لوحة
 * الاستضافة من شاشة صغيرة متعب ومعرّض للخطأ. فبدلاً منه: شاشة «الإعدادات»
 * داخل التطبيق تكتب هنا، وتُطبَّق فوراً بلا إعادة تشغيل.
 *
 * الأولوية: ما يُحفظ هنا يتقدّم على متغيّرات البيئة، لأنه أحدث وأصرح.
 * والقيم تبقى في قاعدة بيانات خادمك — لا تغادره ولا تصل إليّ.
 *
 * تنبيه للاستضافة بلا قرص دائم (الخطة المجانية): هذه القيم تُمحى مع كل
 * إعادة تشغيل، لذا تعرض الواجهة نصّ متغيّرات البيئة لتثبيتها في الاستضافة.
 */
import { all, get, run } from '../db.js';
import { config } from '../config.js';
import { log } from '../lib/log.js';
import { record } from './audit.js';
import { resetEganis } from '../connectors/eganis/index.js';
import { HttpError } from '../lib/http.js';

/** الحقول المسموح حفظها، ومكان كل واحد في إعدادات التطبيق */
const FIELDS = {
  eganisDriver: { path: ['eganis', 'driver'], env: 'EGANIS_DRIVER', label: 'وضع الربط' },
  eganisBaseUrl: { path: ['eganis', 'baseUrl'], env: 'EGANIS_BASE_URL', label: 'رابط لوحة eganis' },
  eganisUsername: { path: ['eganis', 'username'], env: 'EGANIS_USERNAME', label: 'اسم المستخدم' },
  eganisPassword: {
    path: ['eganis', 'password'],
    env: 'EGANIS_PASSWORD',
    label: 'كلمة السر',
    secret: true,
  },
  eganisPages: { path: ['eganis', 'pages'], env: 'EGANIS_PAGES', label: 'صفحات اللوحة' },
  fxSource: { path: ['fx', 'source'], env: 'FX_SOURCE', label: 'مصدر سعر الصرف' },
  fxManualRate: { path: ['fx', 'manualRate'], env: 'FX_USD_TRY', label: 'سعر الصرف اليدوي' },
};

export function ensureTable() {
  run(
    `CREATE TABLE IF NOT EXISTS settings (
       key        TEXT PRIMARY KEY,
       value      TEXT NOT NULL,
       updated_at TEXT NOT NULL DEFAULT (datetime('now'))
     )`,
    [],
  );
}

function readAll() {
  ensureTable();
  const rows = all('SELECT key, value FROM settings', []);
  return Object.fromEntries(rows.map((r) => [r.key, r.value]));
}

/** تطبيق المحفوظ على إعدادات التطبيق الجارية */
export function applyStoredSettings() {
  const stored = readAll();
  let applied = 0;
  for (const [key, value] of Object.entries(stored)) {
    const field = FIELDS[key];
    if (!field || value === '') continue;
    const [section, name] = field.path;
    config[section][name] = value;
    applied += 1;
  }
  if (applied) log.info(`الإعدادات: طُبِّق ${applied} إعداداً محفوظاً من قاعدة البيانات`);
  return applied;
}

const normalizeUrl = (value) => String(value || '').trim().replace(/\/+$/, '');

/** القيم الحالية للعرض — بلا كلمات سر */
export function currentSettings() {
  const stored = readAll();
  const view = {};
  for (const [key, field] of Object.entries(FIELDS)) {
    const [section, name] = field.path;
    const live = config[section][name];
    view[key] = field.secret
      ? { set: Boolean(live), label: field.label }
      : { value: live ?? '', label: field.label, fromApp: stored[key] !== undefined };
  }
  return {
    fields: view,
    /** أسطر جاهزة للصق في إعدادات الاستضافة كي تبقى بعد إعادة التشغيل */
    envLines: Object.entries(FIELDS)
      .filter(([key, field]) => stored[key] && !field.secret)
      .map(([key, field]) => `${field.env}=${stored[key]}`),
    hasStoredSecrets: Object.entries(FIELDS).some(([key, f]) => f.secret && stored[key]),
    note:
      'القيم محفوظة في قاعدة بيانات خادمك. إن كانت استضافتك بلا قرص دائم فستُمحى مع ' +
      'إعادة التشغيل — انسخ الأسطر أدناه إلى متغيّرات البيئة عندك لتثبيتها.',
  };
}

/** حفظ إعدادات وتطبيقها فوراً */
export function saveSettings(input, actor = 'dashboard') {
  ensureTable();
  const changed = [];

  for (const [key, raw] of Object.entries(input || {})) {
    const field = FIELDS[key];
    if (!field) continue;

    let value = String(raw ?? '').trim();
    if (key === 'eganisBaseUrl' && value) {
      value = normalizeUrl(value);
      if (!/^https?:\/\//i.test(value)) {
        throw new HttpError(400, 'رابط اللوحة يجب أن يبدأ بـ https:// أو http://');
      }
    }
    if (key === 'eganisDriver' && value && !['mock', 'api', 'browser'].includes(value)) {
      throw new HttpError(400, `وضع ربط غير معروف: ${value}`);
    }
    // حقل سرّي فارغ = «لا تغيّره»، حتى لا تُمحى كلمة السر بحفظ النموذج
    if (field.secret && !value) continue;

    if (value === '') {
      run('DELETE FROM settings WHERE key = ?', [key]);
    } else {
      run(
        `INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
         ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at`,
        [key, value],
      );
    }
    const [section, name] = field.path;
    config[section][name] = value;
    changed.push(field.label);
  }

  if (changed.length) {
    resetEganis(); // يُعاد بناء الموصل بالإعدادات الجديدة عند أول طلب
    record({
      actor,
      action: 'settings_update',
      target: 'app',
      // لا نسجّل القيم نفسها — بعضها أسرار
      payload: { changed },
    });
    log.info(`الإعدادات: حُدِّث ${changed.join(' · ')}`);
  }

  return { ok: true, changed, settings: currentSettings() };
}
