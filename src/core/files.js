/**
 * إدارة الملفات: ما يرفعه المستخدم في المحادثة، وما يُسحب من eganis (عقود، تأمينات، صور مركبات).
 * الملفات تُحفظ على القرص، وبياناتها في قاعدة البيانات.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { all, get, run } from '../db.js';
import { config } from '../config.js';
import { HttpError } from '../lib/http.js';

const uploadsDir = path.resolve(path.dirname(path.resolve(process.cwd(), config.dbPath)), 'files');
fs.mkdirSync(uploadsDir, { recursive: true });

const MAX_BYTES = 25 * 1024 * 1024; // 25 ميغابايت لكل ملف

/** الصيغ التي يستطيع النموذج قراءتها فعلياً */
export const VIEWABLE_IMAGE = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
export const VIEWABLE_DOC = ['application/pdf'];

/** الصيغ التي يعرضها المتصفح كصورة داخل المحادثة (تشمل SVG الذي لا يقرأه النموذج) */
export const DISPLAY_IMAGE = [...VIEWABLE_IMAGE, 'image/svg+xml'];

const safeName = (name) =>
  String(name || 'ملف')
    .replace(/[/\\?%*:|"<>]/g, '-')
    .slice(0, 120);

/** حفظ ملف من محتوى base64 (الطريقة التي ترفع بها الواجهة) */
export function saveBase64({ name, mime, dataBase64, source = 'upload', ref = null, kind = null }) {
  if (!dataBase64) throw new HttpError(400, 'محتوى الملف مفقود');
  const buffer = Buffer.from(dataBase64, 'base64');
  if (buffer.length > MAX_BYTES) {
    throw new HttpError(413, `حجم الملف يتجاوز الحد (${Math.round(MAX_BYTES / 1024 / 1024)} ميغابايت)`);
  }
  return saveBuffer({ name, mime, buffer, source, ref, kind });
}

export function saveBuffer({ name, mime, buffer, source = 'upload', ref = null, kind = null }) {
  const id = crypto.randomUUID();
  const clean = safeName(name);
  const filePath = path.join(uploadsDir, `${id}-${clean}`);
  fs.writeFileSync(filePath, buffer);
  run(
    `INSERT INTO files (id, name, mime, size, path, source, ref, kind)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
    [id, clean, mime || 'application/octet-stream', buffer.length, filePath, source, ref, kind],
  );
  return getFile(id);
}

export function getFile(id) {
  const row = get('SELECT * FROM files WHERE id = ?', [id]);
  if (!row) throw new HttpError(404, `لا يوجد ملف بالمعرّف ${id}`);
  return row;
}

export function readFile(id) {
  const row = getFile(id);
  if (!fs.existsSync(row.path)) throw new HttpError(410, `الملف "${row.name}" لم يعد موجوداً على القرص`);
  return { ...row, buffer: fs.readFileSync(row.path) };
}

export function listFiles({ limit = 50 } = {}) {
  return all('SELECT id, name, mime, size, source, ref, kind, created_at FROM files ORDER BY created_at DESC LIMIT ?', [
    limit,
  ]);
}

/** وصف مختصر للملف يُعرض في المحادثة */
export function describe(row) {
  return {
    id: row.id,
    name: row.name,
    mime: row.mime,
    size: row.size,
    kind: row.kind,
    ref: row.ref,
    source: row.source,
    url: `/api/files/${row.id}`,
    isImage: DISPLAY_IMAGE.includes(row.mime),
    isPdf: VIEWABLE_DOC.includes(row.mime),
    isVideo: String(row.mime).startsWith('video/'),
    isAudio: String(row.mime).startsWith('audio/'),
  };
}

/** هل يستطيع النموذج «رؤية» محتوى هذا الملف؟ */
export function isModelReadable(mime) {
  return VIEWABLE_IMAGE.includes(mime) || VIEWABLE_DOC.includes(mime);
}
