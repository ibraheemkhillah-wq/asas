import { all, run } from '../db.js';
import { log } from '../lib/log.js';

/**
 * تسجيل أي أمر تشغيلي (خصوصاً أوامر التعديل) في سجل مركزي.
 * @param {{actor:string, action:string, target?:string, payload?:any, result?:any, ok?:boolean}} entry
 */
export function record(entry) {
  const { actor, action, target = null, payload = null, result = null, ok = true } = entry;
  run(
    `INSERT INTO audit_log (actor, action, target, payload, result, ok)
     VALUES (?, ?, ?, ?, ?, ?)`,
    [
      actor,
      action,
      target,
      payload == null ? null : JSON.stringify(payload),
      result == null ? null : JSON.stringify(result),
      ok ? 1 : 0,
    ],
  );
  log.info(`audit: ${actor} → ${action}${target ? ` (${target})` : ''}${ok ? '' : ' [فشل]'}`);
}

export function recentAudit(limit = 100) {
  return all('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?', [Math.min(limit, 500)]).map(
    (row) => ({
      ...row,
      ok: !!row.ok,
      payload: row.payload ? JSON.parse(row.payload) : null,
      result: row.result ? JSON.parse(row.result) : null,
    }),
  );
}
