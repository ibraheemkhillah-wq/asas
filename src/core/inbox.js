/**
 * صندوق واتساب: المحادثات، الرسائل، والردود المدرَّبة.
 */
import { all, get, run } from '../db.js';
import { whatsapp } from '../connectors/whatsapp/index.js';
import { record } from './audit.js';
import { HttpError } from '../lib/http.js';

const normalizePhone = (phone) => String(phone || '').replace(/\D/g, '');

export function upsertConversation(phone, name) {
  const digits = normalizePhone(phone);
  const existing = get('SELECT * FROM conversations WHERE phone = ?', [digits]);
  if (existing) {
    if (name && !existing.name) {
      run('UPDATE conversations SET name = ? WHERE id = ?', [name, existing.id]);
      existing.name = name;
    }
    return existing;
  }
  run('INSERT INTO conversations (phone, name) VALUES (?, ?)', [digits, name || null]);
  return get('SELECT * FROM conversations WHERE phone = ?', [digits]);
}

export function listConversations({ status, limit = 50 } = {}) {
  const sql = status
    ? 'SELECT * FROM conversations WHERE status = ? ORDER BY COALESCE(last_at, created_at) DESC LIMIT ?'
    : 'SELECT * FROM conversations ORDER BY COALESCE(last_at, created_at) DESC LIMIT ?';
  const params = status ? [status, limit] : [limit];
  return all(sql, params);
}

export function getConversation(id) {
  const conversation = get('SELECT * FROM conversations WHERE id = ?', [id]);
  if (!conversation) throw new HttpError(404, `لا توجد محادثة بالرقم ${id}`);
  return conversation;
}

export function getMessages(conversationId, limit = 100) {
  return all(
    'SELECT * FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?',
    [conversationId, limit],
  ).reverse();
}

function touchConversation(id, preview, { unread = false } = {}) {
  run(
    `UPDATE conversations
     SET last_message = ?, last_at = datetime('now'), unread = CASE WHEN ? THEN unread + 1 ELSE 0 END
     WHERE id = ?`,
    [preview.slice(0, 200), unread ? 1 : 0, id],
  );
}

/** تسجيل رسالة واردة من العميل */
export function recordInbound({ phone, name, body, waMessageId }) {
  const conversation = upsertConversation(phone, name);
  run(
    `INSERT INTO messages (conversation_id, direction, body, wa_message_id, status, author)
     VALUES (?, 'in', ?, ?, 'received', 'customer')`,
    [conversation.id, body, waMessageId || null],
  );
  if (conversation.status === 'closed') {
    run("UPDATE conversations SET status = 'open' WHERE id = ?", [conversation.id]);
  }
  touchConversation(conversation.id, body, { unread: true });
  return { conversation: getConversation(conversation.id), body };
}

/** حفظ مسوّدة رد (من الذكاء الاصطناعي أو الموظف) بدون إرسال */
export function saveDraft(conversationId, body, author = 'ai', meta = null) {
  getConversation(conversationId);
  run(
    `INSERT INTO messages (conversation_id, direction, body, status, author, meta)
     VALUES (?, 'out', ?, 'draft', ?, ?)`,
    [conversationId, body, author, meta ? JSON.stringify(meta) : null],
  );
  return get('SELECT * FROM messages WHERE id = last_insert_rowid()');
}

/** إرسال رسالة فعلياً عبر واتساب وتسجيلها */
export async function sendMessage(conversationId, body, author = 'agent') {
  const conversation = getConversation(conversationId);
  const result = await whatsapp().sendText(conversation.phone, body);
  run(
    `INSERT INTO messages (conversation_id, direction, body, wa_message_id, status, author)
     VALUES (?, 'out', ?, ?, 'sent', ?)`,
    [conversationId, body, result.id || null, author],
  );
  touchConversation(conversationId, body);
  record({
    actor: author,
    action: 'whatsapp_send',
    target: conversation.phone,
    payload: { body },
    result: { id: result.id },
  });
  return { ok: true, id: result.id, conversationId };
}

/** إرسال ملف (PDF مثلاً) في محادثة العميل وتسجيله في سجل المحادثة */
export async function sendDocument(conversationId, file, caption = '', author = 'agent') {
  const conversation = getConversation(conversationId);
  const driver = whatsapp();
  if (typeof driver.sendDocument !== 'function') {
    throw new HttpError(501, `سائق واتساب "${driver.name}" لا يدعم إرسال الملفات`);
  }

  const result = await driver.sendDocument(conversation.phone, {
    path: file.path,
    filename: file.name,
    mime: file.mime,
    caption,
  });

  const body = caption ? `${caption}\n📎 ${file.name}` : `📎 ${file.name}`;
  run(
    `INSERT INTO messages (conversation_id, direction, body, wa_message_id, status, author, meta)
     VALUES (?, 'out', ?, ?, 'sent', ?, ?)`,
    [conversationId, body, result.id || null, author, JSON.stringify({ fileId: file.id, kind: 'document' })],
  );
  touchConversation(conversationId, body);
  record({
    actor: author,
    action: 'whatsapp_send_document',
    target: conversation.phone,
    payload: { file: file.name, caption },
    result: { id: result.id },
  });
  return { ok: true, id: result.id, conversationId, fileId: file.id };
}

export function setConversationStatus(id, status, assignedTo = null) {
  const allowed = ['open', 'pending', 'closed'];
  if (!allowed.includes(status)) throw new HttpError(400, `حالة غير مدعومة: ${status}`);
  run('UPDATE conversations SET status = ?, assigned_to = COALESCE(?, assigned_to) WHERE id = ?', [
    status,
    assignedTo,
    id,
  ]);
  return getConversation(id);
}

// ===== الردود المدرَّبة =====

export function listTemplates({ activeOnly = false } = {}) {
  return all(
    activeOnly
      ? 'SELECT * FROM reply_templates WHERE active = 1 ORDER BY used_count DESC, id DESC'
      : 'SELECT * FROM reply_templates ORDER BY id DESC',
  );
}

export function addTemplate({ intent, sampleIn, reply, notes }) {
  if (!intent || !reply) throw new HttpError(400, 'الحقلان intent و reply مطلوبان');
  run(
    'INSERT INTO reply_templates (intent, sample_in, reply, notes) VALUES (?, ?, ?, ?)',
    [intent, sampleIn || null, reply, notes || null],
  );
  const created = get('SELECT * FROM reply_templates WHERE id = last_insert_rowid()');
  record({ actor: 'dashboard', action: 'add_reply_template', target: intent, payload: { reply } });
  return created;
}

export function updateTemplate(id, fields) {
  const current = get('SELECT * FROM reply_templates WHERE id = ?', [id]);
  if (!current) throw new HttpError(404, `لا يوجد قالب بالرقم ${id}`);
  const next = {
    intent: fields.intent ?? current.intent,
    sample_in: fields.sampleIn ?? current.sample_in,
    reply: fields.reply ?? current.reply,
    notes: fields.notes ?? current.notes,
    active: fields.active === undefined ? current.active : fields.active ? 1 : 0,
  };
  run(
    'UPDATE reply_templates SET intent = ?, sample_in = ?, reply = ?, notes = ?, active = ? WHERE id = ?',
    [next.intent, next.sample_in, next.reply, next.notes, next.active, id],
  );
  return get('SELECT * FROM reply_templates WHERE id = ?', [id]);
}

export function deleteTemplate(id) {
  run('DELETE FROM reply_templates WHERE id = ?', [id]);
  return { ok: true };
}

export function markTemplateUsed(id) {
  run('UPDATE reply_templates SET used_count = used_count + 1 WHERE id = ?', [id]);
}
