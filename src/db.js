import { DatabaseSync } from 'node:sqlite';
import fs from 'node:fs';
import path from 'node:path';
import { config } from './config.js';

const dbFile = path.resolve(process.cwd(), config.dbPath);
fs.mkdirSync(path.dirname(dbFile), { recursive: true });

export const db = new DatabaseSync(dbFile);

db.exec('PRAGMA journal_mode = WAL');
db.exec('PRAGMA foreign_keys = ON');

db.exec(`
CREATE TABLE IF NOT EXISTS conversations (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  phone         TEXT NOT NULL UNIQUE,
  name          TEXT,
  status        TEXT NOT NULL DEFAULT 'open',      -- open | pending | closed
  assigned_to   TEXT,
  last_message  TEXT,
  last_at       TEXT,
  unread        INTEGER NOT NULL DEFAULT 0,
  tags          TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  direction       TEXT NOT NULL,                   -- in | out
  body            TEXT NOT NULL,
  wa_message_id   TEXT,
  status          TEXT NOT NULL DEFAULT 'received',-- received | draft | sent | failed
  author          TEXT NOT NULL DEFAULT 'customer',-- customer | agent | ai
  meta            TEXT,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, id);

-- الردود المدرَّبة: قوالب بشرية يستخدمها الذكاء الاصطناعي كأمثلة
CREATE TABLE IF NOT EXISTS reply_templates (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  intent      TEXT NOT NULL,                       -- سبب التواصل: سعر، توفر، حادث، تمديد...
  sample_in   TEXT,                                -- رسالة عميل نموذجية
  reply       TEXT NOT NULL,                       -- الرد البشري المعتمد
  notes       TEXT,
  active      INTEGER NOT NULL DEFAULT 1,
  used_count  INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- سجل كل أمر تشغيلي نُفّذ من خلال النظام
CREATE TABLE IF NOT EXISTS audit_log (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  actor      TEXT NOT NULL,                        -- dashboard | mcp | api | system
  action     TEXT NOT NULL,
  target     TEXT,
  payload    TEXT,
  result     TEXT,
  ok         INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(id DESC);

-- أسعار الصرف المحفوظة (دولار/ليرة) مع مصدر كل سعر ووقته
CREATE TABLE IF NOT EXISTS fx_rates (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  pair       TEXT NOT NULL DEFAULT 'USD/TRY',
  rate       REAL NOT NULL,
  source     TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- المحادثة المباشرة بين المستخدم والمساعد (Claude)
CREATE TABLE IF NOT EXISTS assistant_messages (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  role        TEXT NOT NULL,                     -- user | assistant | system
  body        TEXT NOT NULL DEFAULT '',
  attachments TEXT,                              -- JSON: قائمة معرّفات الملفات
  tools_used  TEXT,                              -- JSON: أسماء الأدوات التي استُخدمت
  created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_assistant_created ON assistant_messages(id);

-- الملفات: مرفوعة من المستخدم أو مسحوبة من eganis
CREATE TABLE IF NOT EXISTS files (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  mime       TEXT NOT NULL,
  size       INTEGER NOT NULL DEFAULT 0,
  path       TEXT NOT NULL,
  source     TEXT NOT NULL DEFAULT 'upload',     -- upload | eganis | generated
  ref        TEXT,                               -- رقم العقد أو المركبة أو العميل
  kind       TEXT,                               -- contract | insurance | vehicle_photo | id | other
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- دفتر حساب المستأجرين: كل حركة مالية بين الشركة والعميل
-- credit = لصالح العميل (تأمين، دفعة، خصم)
-- debit  = على العميل (أجرة، حادث، مخالفة، أو مبلغ أعدناه له)
CREATE TABLE IF NOT EXISTS ledger_entries (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id   TEXT NOT NULL,
  customer_name TEXT,
  phone         TEXT,
  type          TEXT NOT NULL,
  direction     TEXT NOT NULL,                    -- credit | debit
  amount        REAL NOT NULL CHECK (amount >= 0),
  ref           TEXT,                             -- رقم العقد أو المرجع
  note          TEXT,
  occurred_at   TEXT NOT NULL,                    -- تاريخ الحركة
  source        TEXT NOT NULL DEFAULT 'manual',   -- manual | eganis
  author        TEXT NOT NULL DEFAULT 'dashboard',
  voided        INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_ledger_customer ON ledger_entries(customer_id, occurred_at);

-- ملاحظات تشغيلية مرتبطة بعقد/مركبة/عميل
CREATE TABLE IF NOT EXISTS notes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  ref_type   TEXT NOT NULL,                        -- contract | vehicle | customer | booking
  ref_id     TEXT NOT NULL,
  body       TEXT NOT NULL,
  author     TEXT NOT NULL DEFAULT 'system',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_notes_ref ON notes(ref_type, ref_id);
`);

/** ترقيات بسيطة للمخطط تعمل على قواعد بيانات أُنشئت قبل إضافة الأعمدة */
function addColumnIfMissing(table, column, definition) {
  const columns = db.prepare(`PRAGMA table_info(${table})`).all();
  if (!columns.some((c) => c.name === column)) {
    db.exec(`ALTER TABLE ${table} ADD COLUMN ${column} ${definition}`);
  }
}

addColumnIfMissing('ledger_entries', 'currency', "TEXT NOT NULL DEFAULT 'TRY'");

export function all(sql, params = []) {
  return db.prepare(sql).all(...params);
}

export function get(sql, params = []) {
  return db.prepare(sql).get(...params);
}

export function run(sql, params = []) {
  return db.prepare(sql).run(...params);
}
