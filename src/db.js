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

export function all(sql, params = []) {
  return db.prepare(sql).all(...params);
}

export function get(sql, params = []) {
  return db.prepare(sql).get(...params);
}

export function run(sql, params = []) {
  return db.prepare(sql).run(...params);
}
