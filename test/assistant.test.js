import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'callrent-asst-'));
process.env.DB_PATH = path.join(tmp, 'test.db');
process.env.EGANIS_DRIVER = 'mock';
process.env.WHATSAPP_DRIVER = 'mock';
process.env.ALLOW_WRITES = 'true';

const { buildTools, listMessages, clearMessages } = await import('../src/ai/assistant.js');
const files = await import('../src/core/files.js');
const { eganis } = await import('../src/connectors/eganis/index.js');

function toolsFor() {
  const session = { attachments: [] };
  const list = buildTools(session);
  return { session, byName: new Map(list.map((t) => [t.name, t])) };
}

test('المستندات تُقرأ من eganis مع تصفية بالمركبة', async () => {
  const { byName } = toolsFor();
  const docs = await byName.get('list_documents').run({ plate: '1234-567' });
  assert.ok(docs.length >= 3);
  assert.ok(docs.some((d) => d.kind === 'contract'));
  assert.ok(docs.some((d) => d.kind === 'insurance'));
  assert.ok(docs.some((d) => d.kind === 'vehicle_photo'));
  assert.ok(docs.every((d) => d.plate === '1234-567' || d.contractNo));
});

test('send_files ينزّل الملف من eganis ويسلّمه للمحادثة', async () => {
  const { session, byName } = toolsFor();
  const docs = await byName.get('list_documents').run({ plate: '3456-789', type: 'vehicle_photo' });
  const result = await byName.get('send_files').run({ documentIds: [docs[0].id] });

  assert.equal(result.sent.length, 1);
  assert.equal(session.attachments.length, 1);

  const attached = session.attachments[0];
  assert.equal(attached.source, 'eganis');
  assert.ok(attached.url.startsWith('/api/files/'));

  const stored = files.readFile(attached.id);
  assert.ok(stored.buffer.length > 0);
});

test('أدوات المحاسبة والعمليات موصولة بنفس منطق التطبيق', async () => {
  const { byName } = toolsFor();
  const stmt = await byName.get('customer_statement').run({ q: 'أحمد نصار' });
  assert.equal(stmt.found, true);
  assert.ok(stmt.text.includes('كشف حساب'));

  const overview = await byName.get('ops_overview').run({});
  assert.ok(Number.isFinite(overview.counters.vehiclesAvailable));

  const contracts = await byName.get('list_contracts').run({ status: 'open' });
  assert.ok(contracts.every((c) => c.status === 'open'));
});

test('كل أداة تحمل وصفاً ومخطط مدخلات صالحاً', () => {
  const { byName } = toolsFor();
  for (const [name, tool] of byName) {
    assert.ok(tool.description && tool.description.length > 10, `${name} بلا وصف`);
    assert.equal(tool.input_schema.type, 'object', `${name} مخطط غير صالح`);
    assert.equal(typeof tool.run, 'function');
  }
});

test('الملفات المرفوعة تُحفظ وتُقرأ ويُعرف ما يستطيع النموذج رؤيته', () => {
  const saved = files.saveBase64({
    name: 'ملاحظة.txt',
    mime: 'text/plain',
    dataBase64: Buffer.from('تجربة').toString('base64'),
  });
  assert.equal(files.readFile(saved.id).buffer.toString('utf8'), 'تجربة');
  assert.equal(files.isModelReadable('image/png'), true);
  assert.equal(files.isModelReadable('application/pdf'), true);
  assert.equal(files.isModelReadable('video/mp4'), false);
});

test('سجل المحادثة يُحفظ ويُمسح', () => {
  clearMessages();
  assert.equal(listMessages().length, 0);
});

test('الموصل يوفّر تنزيل المستندات بصيغة قابلة للحفظ', async () => {
  const driver = eganis();
  const docs = await driver.listDocuments({ contractNo: 'CR-2041' });
  const file = await driver.downloadDocument(docs[0].id);
  assert.ok(file.buffer.length > 0);
  assert.ok(file.mime);
  assert.ok(file.name);
});

// ===== حلقة المحادثة كاملة مع نموذج مُحاكى =====
// (لا يمكن استدعاء Claude الحقيقي في الاختبارات، لكن هذه الحلقة هي قلب الميزة:
//  استدعاء أداة ← تنفيذها ← إعادة النتيجة ← ردّ نهائي مع مرفقات)

const { ask, __setClient } = await import('../src/ai/assistant.js');

test('المحادثة تنفّذ الأدوات وتوصل الملفات وتحفظ السجل', async () => {
  clearMessages();
  const seen = { requests: [] };

  __setClient({
    messages: {
      async create(params) {
        seen.requests.push(params);
        if (seen.requests.length === 1) {
          // الجولة الأولى: يطلب المستندات ثم يرسلها
          return {
            stop_reason: 'tool_use',
            content: [
              { type: 'text', text: 'أبحث عن مستندات المركبة…' },
              {
                type: 'tool_use',
                id: 'tu_1',
                name: 'list_documents',
                input: { plate: '6789-012', type: 'vehicle_photo' },
              },
            ],
          };
        }
        if (seen.requests.length === 2) {
          const docs = JSON.parse(
            params.messages.at(-1).content.find((c) => c.tool_use_id === 'tu_1').content,
          );
          return {
            stop_reason: 'tool_use',
            content: [
              {
                type: 'tool_use',
                id: 'tu_2',
                name: 'send_files',
                input: { documentIds: [docs[0].id] },
              },
            ],
          };
        }
        return {
          stop_reason: 'end_turn',
          content: [{ type: 'text', text: 'تفضّل صورة المركبة 6789-012.' }],
        };
      },
    },
  });

  const result = await ask({ text: 'ابعتلي صور المركبة 6789-012' });

  assert.equal(result.reply, 'تفضّل صورة المركبة 6789-012.');
  assert.deepEqual(result.toolsUsed, ['list_documents', 'send_files']);
  assert.equal(result.attachments.length, 1);
  assert.ok(result.attachments[0].url.startsWith('/api/files/'));

  // النموذج تلقّى الأدوات ومطالبة النظام
  assert.ok(seen.requests[0].tools.some((t) => t.name === 'customer_statement'));
  assert.match(seen.requests[0].system[0].text, /eganis/);

  // السجل محفوظ: رسالة المستخدم ثم رد المساعد بمرفقه
  const saved = listMessages();
  assert.equal(saved.length, 2);
  assert.equal(saved[0].role, 'user');
  assert.equal(saved[1].role, 'assistant');
  assert.equal(saved[1].attachments.length, 1);

  __setClient(null);
});

test('فشل النموذج يُحفظ في المحادثة بدل أن يختفي', async () => {
  clearMessages();
  __setClient({
    messages: {
      async create() {
        throw new Error('انقطاع في الاتصال');
      },
    },
  });

  await assert.rejects(() => ask({ text: 'اختبار' }), /انقطاع/);
  const saved = listMessages();
  assert.equal(saved.at(-1).role, 'assistant');
  assert.match(saved.at(-1).body, /تعذّر التنفيذ/);

  __setClient(null);
});
