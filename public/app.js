const app = document.getElementById('app');
const toastEl = document.getElementById('toast');
const statusPill = document.getElementById('status-pill');

const state = {
  view: 'today',
  token: localStorage.getItem('appToken') || '',
  conversationId: null,
  accountingQuery: '',
  accountingCustomer: null,
  lastRender: 0,
};

// ===== أدوات =====

function toast(message, isError = false) {
  toastEl.textContent = message;
  toastEl.className = `toast${isError ? ' error' : ''}`;
  toastEl.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (toastEl.hidden = true), 4000);
}

async function api(path, { method = 'GET', body } = {}) {
  const res = await fetch(path, {
    method,
    headers: {
      ...(state.token ? { Authorization: `Bearer ${state.token}` } : {}),
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `خطأ ${res.status}`);
  return data;
}

const esc = (value) =>
  String(value ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );

const SYMBOL = { TRY: '₺', USD: '$' };
const cur = (c) => (String(c || '').toUpperCase() === 'USD' ? 'USD' : 'TRY');

const money = (n, currency = 'TRY') =>
  `<bdi dir="ltr">${Number(n || 0).toLocaleString('en-US', { maximumFractionDigits: 2 })} ${
    SYMBOL[cur(currency)]
  }</bdi>`;

/** «2,350 ₺ / 50 $» — العرض المزدوج المعتمد في كل الحسابات */
const dualMoney = (amounts = {}, { hideZero = false } = {}) => {
  const parts = [];
  const t = Number(amounts.TRY || 0);
  const u = Number(amounts.USD || 0);
  if (!hideZero || t) parts.push(money(t, 'TRY'));
  if (!hideZero || u) parts.push(money(u, 'USD'));
  if (!parts.length) parts.push(money(0, 'TRY'));
  // مسافة غير فاصلة قبل الشرطة حتى لا تنزل وحدها على سطر جديد
  return parts.join('&nbsp;<span class="muted">/</span> ');
};

const fmtDate = (value) =>
  value
    ? new Date(value).toLocaleString('ar-EG-u-nu-latn', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—';

const labels = {
  open: 'مفتوح',
  overdue: 'متأخر',
  closed: 'مغلق',
  reserved: 'محجوز',
  available: 'متاحة',
  rented: 'مؤجّرة',
  maintenance: 'صيانة',
  out_of_service: 'خارج الخدمة',
  pending: 'قيد التنفيذ',
  done: 'منجزة',
  new: 'جديد',
  confirmed: 'مؤكد',
  cancelled: 'ملغى',
  delivery: 'تسليم',
  pickup: 'استلام',
  draft: 'مسوّدة',
  sent: 'مُرسلة',
  received: 'واردة',
};
const label = (key) => labels[key] || key || '—';
const badge = (key) => `<span class="badge ${esc(key)}">${esc(label(key))}</span>`;

/** على شاشات الموبايل تتحول صفوف الجدول إلى بطاقات، فنضيف اسم كل عمود داخل الخلية */
function labelTables(root = app) {
  root.querySelectorAll('table').forEach((tableEl) => {
    const headers = [...tableEl.querySelectorAll('thead th')].map((th) => th.textContent.trim());
    tableEl.querySelectorAll('tbody tr').forEach((tr) => {
      [...tr.children].forEach((td, index) => {
        if (headers[index] && !td.dataset.label) td.dataset.label = headers[index];
      });
    });
  });
}
new MutationObserver(() => labelTables()).observe(app, { childList: true, subtree: true });

function table(columns, rows, renderRow) {
  if (!rows.length) return '<div class="empty">لا توجد بيانات</div>';
  return `<div class="table-wrap"><table>
    <thead><tr>${columns.map((c) => `<th>${esc(c)}</th>`).join('')}</tr></thead>
    <tbody>${rows.map(renderRow).join('')}</tbody>
  </table></div>`;
}

// ===== العروض =====

async function viewToday() {
  const data = await api('/api/ops/overview');
  const c = data.counters;
  const kpi = (value, text, cls = '') =>
    `<div class="card"><div class="kpi-value ${cls}">${value}</div><div class="kpi-label">${text}</div></div>`;

  app.innerHTML = `
    <div class="grid kpi">
      ${kpi(c.overdue, 'عقود متأخرة', c.overdue ? 'danger' : 'ok')}
      ${kpi(c.dueToday, 'إرجاعات اليوم', c.dueToday ? 'warn' : '')}
      ${kpi(c.pickupsToday, 'تسليمات اليوم')}
      ${kpi(c.tasksToday, 'مهام اليوم')}
      ${kpi(c.vehiclesAvailable, 'مركبات متاحة', c.vehiclesAvailable ? 'ok' : 'danger')}
      ${kpi(c.vehiclesRented, 'مركبات مؤجّرة')}
      ${kpi(c.vehiclesMaintenance, 'في الصيانة', c.vehiclesMaintenance ? 'warn' : '')}
      ${kpi(
        dualMoney(c.unpaidBalance, { hideZero: true }),
        'رصيد غير محصّل',
        c.unpaidBalance.TRY || c.unpaidBalance.USD ? 'warn' : 'ok',
      )}
    </div>

    ${
      data.alerts.length
        ? `<div class="card" style="margin-top:14px">
            <h2>تنبيهات</h2>
            ${data.alerts.map((a) => `<div class="alert ${esc(a.level)}">${esc(a.text)}</div>`).join('')}
          </div>`
        : ''
    }

    <div class="grid two" style="margin-top:14px">
      <div class="card">
        <h2>عقود متأخرة</h2>
        ${table(['العقد', 'العميل', 'اللوحة', 'الإرجاع', 'الرصيد'], data.overdue, (r) => `
          <tr>
            <td>${esc(r.no)}</td><td>${esc(r.customerName)}</td><td>${esc(r.plate)}</td>
            <td>${fmtDate(r.endAt)}</td><td>${money(r.balance, r.currency)}</td>
          </tr>`)}
      </div>

      <div class="card">
        <h2>إرجاعات مستحقة اليوم</h2>
        ${table(['العقد', 'العميل', 'اللوحة', 'الوقت'], data.dueToday, (r) => `
          <tr><td>${esc(r.no)}</td><td>${esc(r.customerName)}</td><td>${esc(r.plate)}</td><td>${fmtDate(r.endAt)}</td></tr>`)}
      </div>

      <div class="card">
        <h2>تسليمات اليوم</h2>
        ${table(['الحجز', 'العميل', 'الفئة', 'الوقت', 'الحالة'], data.pickupsToday, (r) => `
          <tr><td>${esc(r.no)}</td><td>${esc(r.customerName)}</td><td>${esc(r.group)}</td>
          <td>${fmtDate(r.pickupAt)}</td><td>${badge(r.status)}</td></tr>`)}
      </div>

      <div class="card">
        <h2>مهام اليوم</h2>
        ${table(['النوع', 'المرجع', 'اللوحة', 'الوقت', 'السائق'], data.tasksToday, (r) => `
          <tr><td>${badge(r.type)}</td><td>${esc(r.ref)}</td><td>${esc(r.plate)}</td>
          <td>${fmtDate(r.at)}</td><td>${esc(r.driver || '—')}</td></tr>`)}
      </div>
    </div>`;
}

async function viewContracts() {
  app.innerHTML = `
    <div class="toolbar">
      <input id="q" placeholder="بحث بالاسم أو الهاتف أو اللوحة…" />
      <select id="status">
        <option value="">كل الحالات</option>
        <option value="open">مفتوح</option>
        <option value="overdue">متأخر</option>
        <option value="closed">مغلق</option>
      </select>
      <button class="btn" id="search">بحث</button>
    </div>
    <div class="card" id="results"><div class="empty">جارِ التحميل…</div></div>`;

  async function load() {
    const q = document.getElementById('q').value.trim();
    const status = document.getElementById('status').value;
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (status) params.set('status', status);
    const rows = await api(`/api/ops/contracts?${params}`);
    document.getElementById('results').innerHTML = table(
      ['العقد', 'العميل', 'الهاتف', 'اللوحة', 'من', 'إلى', 'الحالة', 'الرصيد', 'إجراءات'],
      rows,
      (r) => `
        <tr>
          <td>${esc(r.no)}</td><td>${esc(r.customerName)}</td><td>${esc(r.phone)}</td>
          <td>${esc(r.plate)}</td><td>${fmtDate(r.startAt)}</td><td>${fmtDate(r.endAt)}</td>
          <td>${badge(r.status)}</td><td>${money(r.balance, r.currency)}</td>
          <td class="row">
            <button class="btn small" data-extend="${esc(r.no)}">تمديد</button>
            ${r.status !== 'closed' ? `<button class="btn small ghost" data-close="${esc(r.no)}">إغلاق</button>` : ''}
          </td>
        </tr>`,
    );
  }

  document.getElementById('search').onclick = () => load().catch((e) => toast(e.message, true));
  document.getElementById('q').onkeydown = (e) => {
    if (e.key === 'Enter') load().catch((err) => toast(err.message, true));
  };

  app.addEventListener('click', async (event) => {
    const extendId = event.target.dataset?.extend;
    const closeId = event.target.dataset?.close;
    try {
      if (extendId) {
        const days = prompt(`تمديد العقد ${extendId} — عدد الأيام:`, '1');
        if (!days) return;
        await api(`/api/ops/contracts/${encodeURIComponent(extendId)}/extend`, {
          method: 'POST',
          body: { days: Number(days) },
        });
        toast('تم تمديد العقد');
        await load();
      } else if (closeId) {
        const odometer = prompt(`إغلاق العقد ${closeId} — قراءة العدّاد:`, '');
        if (odometer === null) return;
        await api(`/api/ops/contracts/${encodeURIComponent(closeId)}/close`, {
          method: 'POST',
          body: { odometer: Number(odometer) || undefined },
        });
        toast('تم إغلاق العقد وإعادة المركبة للأسطول');
        await load();
      }
    } catch (err) {
      toast(err.message, true);
    }
  });

  await load();
}

async function viewFleet() {
  const vehicles = await api('/api/ops/vehicles');
  const statuses = ['available', 'rented', 'maintenance', 'out_of_service'];
  app.innerHTML = `<div class="card">
    <h2>الأسطول (${vehicles.length} مركبة)</h2>
    ${table(
      ['اللوحة', 'المركبة', 'السنة', 'الفئة', 'الفرع', 'العدّاد', 'الحالة', 'تغيير الحالة'],
      vehicles,
      (v) => `
        <tr>
          <td>${esc(v.plate)}</td><td>${esc(v.make)} ${esc(v.model)}</td><td>${esc(v.year)}</td>
          <td>${esc(v.group)}</td><td>${esc(v.branch)}</td><td>${esc(v.odometer)}</td>
          <td>${badge(v.status)}</td>
          <td>
            <select data-vehicle="${esc(v.id)}">
              ${statuses
                .map((s) => `<option value="${s}"${s === v.status ? ' selected' : ''}>${label(s)}</option>`)
                .join('')}
            </select>
          </td>
        </tr>`,
    )}
  </div>`;

  app.addEventListener('change', async (event) => {
    const id = event.target.dataset?.vehicle;
    if (!id) return;
    try {
      await api(`/api/ops/vehicles/${encodeURIComponent(id)}/status`, {
        method: 'POST',
        body: { status: event.target.value },
      });
      toast('تم تحديث حالة المركبة');
      render();
    } catch (err) {
      toast(err.message, true);
    }
  });
}

// ===== محادثتنا (المساعد) =====

const QUICK_PROMPTS = [
  'شو المتأخر اليوم؟',
  'ابعتلي عقد أحمد نصار',
  'ابعتلي صور المركبة 1234-567',
  'بوليصة تأمين المركبة 3456-789',
  'قدّيش بدنا من سامي عودة؟',
];

/** روابط الملفات تُفتح من الوسوم مباشرة (img/video/a) فلا تحمل ترويسة الدخول — نمرّر الرمز في الرابط */
function fileUrl(file, { download = false } = {}) {
  const params = new URLSearchParams();
  if (state.token) params.set('token', state.token);
  if (download) params.set('download', '1');
  const query = params.toString();
  return `${file.url}${query ? `?${query}` : ''}`;
}

function fileCard(raw) {
  // نحسب نوع العرض من الـ mime مباشرة حتى لا نعتمد على بيانات محفوظة قديمة
  const mime = String(raw.mime || '');
  const file = {
    ...raw,
    url: fileUrl(raw),
    downloadUrl: fileUrl(raw, { download: true }),
    isImage: mime.startsWith('image/'),
    isVideo: mime.startsWith('video/'),
    isAudio: mime.startsWith('audio/'),
    isPdf: mime === 'application/pdf',
  };
  if (file.isImage) {
    return `<a class="att" href="${esc(file.url)}" target="_blank" rel="noopener">
      <img src="${esc(file.url)}" alt="${esc(file.name)}" loading="lazy" />
      <span>${esc(file.name)}</span>
    </a>`;
  }
  if (file.isVideo) {
    return `<div class="att"><video src="${esc(file.url)}" controls preload="metadata"></video>
      <span>${esc(file.name)}</span></div>`;
  }
  if (file.isAudio) {
    return `<div class="att"><audio src="${esc(file.url)}" controls></audio>
      <span>${esc(file.name)}</span></div>`;
  }
  const icon = file.isPdf ? '📄' : '📎';
  return `<a class="att file" href="${esc(file.downloadUrl)}">
    <span class="ico">${icon}</span>
    <span>${esc(file.name)}<small>${Math.max(1, Math.round((file.size || 0) / 1024))} كيلوبايت</small></span>
  </a>`;
}

async function viewAssistant() {
  const data = await api('/api/assistant/messages');

  app.innerHTML = `
    <div class="card chat-card">
      <div class="row" style="justify-content:space-between;margin-bottom:10px">
        <h2 style="margin:0">محادثتنا</h2>
        <div class="row">
          <span class="badge ${data.ready ? 'open' : 'overdue'}">${data.ready ? 'جاهز' : 'يحتاج مفتاح API'}</span>
          <button class="btn small ghost" id="chat-clear">مسح المحادثة</button>
        </div>
      </div>

      <div class="chat" id="chat">
        ${
          data.messages.length
            ? data.messages.map(renderChatMessage).join('')
            : `<div class="empty">اسألني عن أي شيء في النظام — عقود، مركبات، حسابات، مستندات.<br />
                 أرسل لي صورة أو ملفاً وسأتعامل معه.</div>`
        }
      </div>

      <div class="quick" id="quick">
        ${QUICK_PROMPTS.map((q) => `<button class="chip-btn" data-quick="${esc(q)}">${esc(q)}</button>`).join('')}
      </div>

      <div id="pending" class="pending"></div>

      <div class="composer">
        <textarea id="chat-input" rows="2" placeholder="اكتب رسالتك… (Enter للإرسال، Shift+Enter لسطر جديد)"></textarea>
        <div class="row" style="margin-top:8px">
          <button class="btn" id="chat-send">إرسال</button>
          <button class="btn ghost" id="chat-attach">إرفاق ملف</button>
          <input type="file" id="chat-file" multiple hidden />
          <span class="muted" style="font-size:12.5px">صور و PDF أقرأها · فيديو وصوت وملفات أخرى تُحفظ وتُرسل</span>
        </div>
      </div>
    </div>`;

  const chatBox = document.getElementById('chat');
  const input = document.getElementById('chat-input');
  const pendingBox = document.getElementById('pending');
  chatBox.scrollTop = chatBox.scrollHeight;

  let pending = []; // ملفات مرفوعة بانتظار الإرسال

  function drawPending() {
    pendingBox.innerHTML = pending.length
      ? `<div class="row">${pending
          .map((f, i) => `<span class="chip-btn" data-drop="${i}">${esc(f.name)} ✕</span>`)
          .join('')}</div>`
      : '';
  }

  async function uploadFiles(fileList) {
    for (const file of fileList) {
      try {
        const dataBase64 = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result).split(',')[1]);
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
        const saved = await api('/api/assistant/upload', {
          method: 'POST',
          body: { name: file.name, mime: file.type || 'application/octet-stream', dataBase64 },
        });
        pending.push(saved);
        drawPending();
      } catch (err) {
        toast(`تعذّر رفع ${file.name}: ${err.message}`, true);
      }
    }
  }

  async function send() {
    const text = input.value.trim();
    if (!text && !pending.length) return;
    const fileIds = pending.map((f) => f.id);
    const attachments = [...pending];

    input.value = '';
    pending = [];
    drawPending();

    chatBox.insertAdjacentHTML(
      'beforeend',
      renderChatMessage({ role: 'user', body: text, attachments, created_at: null }) +
        '<div class="msg-a thinking" id="thinking">…أبحث في النظام</div>',
    );
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const result = await api('/api/assistant/message', {
        method: 'POST',
        body: { text, fileIds },
      });
      document.getElementById('thinking')?.remove();
      chatBox.insertAdjacentHTML(
        'beforeend',
        renderChatMessage({
          role: 'assistant',
          body: result.reply,
          attachments: result.attachments,
          tools_used: result.toolsUsed,
          created_at: null,
        }),
      );
      chatBox.scrollTop = chatBox.scrollHeight;
    } catch (err) {
      document.getElementById('thinking')?.remove();
      chatBox.insertAdjacentHTML(
        'beforeend',
        `<div class="msg-a err">${esc(err.message)}</div>`,
      );
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }

  document.getElementById('chat-send').onclick = send;
  input.onkeydown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };
  document.getElementById('chat-attach').onclick = () => document.getElementById('chat-file').click();
  document.getElementById('chat-file').onchange = (event) => uploadFiles([...event.target.files]);

  document.getElementById('quick').onclick = (event) => {
    const q = event.target.dataset?.quick;
    if (!q) return;
    input.value = q;
    send();
  };

  pendingBox.onclick = (event) => {
    const index = event.target.dataset?.drop;
    if (index === undefined) return;
    pending.splice(Number(index), 1);
    drawPending();
  };

  document.getElementById('chat-clear').onclick = async () => {
    if (!confirm('مسح كل رسائل المحادثة؟')) return;
    await api('/api/assistant/messages', { method: 'DELETE' });
    render();
  };

  // السحب والإفلات
  chatBox.ondragover = (e) => e.preventDefault();
  chatBox.ondrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer?.files?.length) uploadFiles([...e.dataTransfer.files]);
  };
}

function renderChatMessage(m) {
  const attachments = (m.attachments || []).map(fileCard).join('');
  const tools = (m.tools_used || []).length
    ? `<div class="tools">${[...new Set(m.tools_used)].map((t) => `<span class="chip-btn">${esc(t)}</span>`).join('')}</div>`
    : '';
  const body = esc(m.body || '').replace(/\n/g, '<br />');
  return `<div class="${m.role === 'user' ? 'msg-u' : 'msg-a'}">
    ${body}
    ${attachments ? `<div class="atts">${attachments}</div>` : ''}
    ${tools}
  </div>`;
}

// ===== محاسبة المستأجرين =====

/** شريط سعر الصرف — يُعرض فوق كل حساب مع مصدره ووقته */
function fxChip(rate) {
  if (!rate || !rate.rate) {
    return `<span class="fx-chip warn">تعذّر جلب سعر الصرف${
      rate?.error ? ` — ${esc(rate.error)}` : ''
    }</span>`;
  }
  const age = rate.ageMinutes > 0 ? `منذ ${rate.ageMinutes} دقيقة` : 'الآن';
  return `<span class="fx-chip ${rate.stale ? 'warn' : ''}">
      سعر الصرف: <bdi dir="ltr">1 $ = ${Number(rate.rate).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4,
      })} ₺</bdi>
      <span class="muted">· ${esc(rate.source)} · ${esc(age)}</span>
      <button class="btn small ghost" id="fx-refresh">تحديث</button>
    </span>`;
}

/** تحديث تلقائي لشريط السعر كل دقيقة ما دام التبويب مفتوحاً */
let fxTicker = null;
function startFxTicker(onRate) {
  clearInterval(fxTicker);
  fxTicker = setInterval(async () => {
    const bar = document.querySelector('.fx-bar');
    if (!bar) return clearInterval(fxTicker);
    if (document.hidden) return;
    try {
      const rate = await api('/api/fx/rate');
      bar.innerHTML = fxChip(rate);
      onRate?.(rate);
    } catch {
      /* الشريط يبقى كما هو حتى المحاولة التالية */
    }
  }, 60000);
}

async function viewAccounting() {
  const [balances, rate] = await Promise.all([
    api('/api/accounting/open-balances'),
    api('/api/fx/rate').catch((err) => ({ error: err.message })),
  ]);

  app.innerHTML = `
    <div class="toolbar">
      <input id="acc-q" placeholder="اكتب اسم العميل أو رقم هاتفه…" value="${esc(state.accountingQuery || '')}" />
      <button class="btn" id="acc-search">عرض الحساب</button>
    </div>
    <div class="fx-bar">${fxChip(rate)}</div>
    <div id="acc-result"></div>
    <div class="card" style="margin-top:14px">
      <h2>حسابات غير مصفّاة</h2>
      <p class="muted">العملاء الذين لهم رصيد عندنا أو عليهم مستحقات — اضغط أي اسم لفتح كشفه. كل مبلغ بعملته الأصلية.</p>
      ${table(['العميل', 'الهاتف', 'تأمينات محفوظة', 'الحالة', 'المبلغ (ليرة / دولار)'], balances, (b) => `
        <tr class="clickable" data-open="${esc(b.customer.name)}">
          <td>${esc(b.customer.name)}</td>
          <td>${esc(b.customer.phone || '—')}</td>
          <td>${dualMoney(b.depositsHeld, { hideZero: true })}</td>
          <td>${
            b.mixed
              ? '<span class="badge pending">له وعليه</span>'
              : b.status === 'company_owes'
                ? '<span class="badge open">له عندنا</span>'
                : '<span class="badge overdue">مطلوب منه</span>'
          }</td>
          <td>${
            b.mixed
              ? `<div class="ok">له ${dualMoney(b.toRefund, { hideZero: true })}</div>
                 <div class="danger">عليه ${dualMoney(b.toCollect, { hideZero: true })}</div>`
              : `<strong>${dualMoney(
                  b.status === 'company_owes' ? b.toRefund : b.toCollect,
                  { hideZero: true },
                )}</strong>`
          }</td>
        </tr>`)}
    </div>`;

  const input = document.getElementById('acc-q');

  /** إعادة رسم شريط السعر وحده دون إعادة بناء الصفحة */
  function bindFxRefresh() {
    const btn = document.getElementById('fx-refresh');
    if (!btn) return;
    btn.onclick = async () => {
      const bar = document.querySelector('.fx-bar');
      btn.disabled = true;
      try {
        const fresh = await api('/api/fx/rate?force=1');
        bar.innerHTML = fxChip(fresh);
        bindFxRefresh();
        toast('تم تحديث سعر الصرف');
        if (state.accountingQuery) await loadStatement(state.accountingQuery);
      } catch (err) {
        toast(err.message, true);
        btn.disabled = false;
      }
    };
  }
  bindFxRefresh();
  startFxTicker(bindFxRefresh);

  async function loadStatement(q) {
    state.accountingQuery = q;
    const box = document.getElementById('acc-result');
    box.innerHTML = '<div class="card"><div class="empty">جارِ حساب الكشف…</div></div>';
    const stmt = await api(`/api/accounting/statement?q=${encodeURIComponent(q)}`);

    if (!stmt.found) {
      box.innerHTML = `<div class="card"><div class="empty">${esc(stmt.message)}</div></div>`;
      return;
    }
    state.accountingCustomer = stmt.customer;

    const headline =
      stmt.status === 'company_owes'
        ? { text: 'مستحق للعميل — نُعيده له', value: stmt.toRefund, cls: 'ok' }
        : stmt.status === 'customer_owes'
          ? { text: 'مطلوب من العميل — نطالبه به', value: stmt.toCollect, cls: 'danger' }
          : { text: 'الحساب مصفّى', value: { TRY: 0, USD: 0 }, cls: '' };

    // المكافئ الإجمالي بسعر اللحظة — للاطّلاع فقط، والأرصدة تبقى بعملتها
    const sign = stmt.status === 'customer_owes' ? -1 : 1;
    const equivalent =
      stmt.combined && stmt.status !== 'settled'
        ? `<div class="muted" style="margin-top:6px">${
            stmt.mixed ? 'صافي الفرق' : 'أي ما يعادل'
          } ${money(sign * stmt.combined.inTRY, 'TRY')} أو ${money(
            sign * stmt.combined.inUSD,
            'USD',
          )}</div>`
        : '';

    const byCur = (field) => ({ TRY: stmt.byCurrency.TRY[field], USD: stmt.byCurrency.USD[field] });

    box.innerHTML = `
      <div class="card">
        <div class="row" style="justify-content:space-between;align-items:flex-start">
          <div>
            <h2 style="margin-bottom:4px">${esc(stmt.customer.name)}</h2>
            <div class="muted">${esc(stmt.customer.phone || '')} ${
              stmt.customer.idNumber ? `· هوية ${esc(stmt.customer.idNumber)}` : ''
            }</div>
          </div>
          <div style="text-align:center">
            ${
              stmt.mixed
                ? `<div class="kpi-value ok">${dualMoney(stmt.toRefund, { hideZero: true })}</div>
                   <div class="kpi-label">مستحق له عندنا</div>
                   <div class="kpi-value danger" style="margin-top:8px">${dualMoney(stmt.toCollect, { hideZero: true })}</div>
                   <div class="kpi-label">مستحق علينا منه</div>`
                : `<div class="kpi-value ${headline.cls}">${dualMoney(headline.value, {
                    hideZero: stmt.status !== 'settled',
                  })}</div>
                   <div class="kpi-label">${esc(headline.text)}</div>`
            }
            ${equivalent}
          </div>
        </div>

        <div class="grid kpi" style="margin-top:14px">
          <div class="card"><div class="kpi-value">${dualMoney(byCur('depositsHeld'), { hideZero: true })}</div><div class="kpi-label">تأمينات محفوظة</div></div>
          <div class="card"><div class="kpi-value">${dualMoney(byCur('credits'), { hideZero: true })}</div><div class="kpi-label">إجمالي ما دفعه</div></div>
          <div class="card"><div class="kpi-value">${dualMoney(byCur('debits'), { hideZero: true })}</div><div class="kpi-label">إجمالي المستحقات عليه</div></div>
          <div class="card"><div class="kpi-value ${
            stmt.byCurrency.TRY.damages || stmt.byCurrency.USD.damages ? 'warn' : ''
          }">${dualMoney(byCur('damages'), { hideZero: true })}</div><div class="kpi-label">تكاليف حوادث</div></div>
        </div>

        <div class="row" style="margin-top:14px">
          <button class="btn" id="acc-send-pdf">إرسال PDF على واتساب</button>
          <button class="btn ghost" id="acc-pdf">فتح / حفظ PDF</button>
          <button class="btn ghost" id="acc-send">إرسال الكشف نصاً</button>
          <button class="btn ghost" id="acc-copy">نسخ الكشف</button>
          <button class="btn ghost" id="acc-add">إضافة حركة</button>
          ${stmt.status !== 'settled' ? '<button class="btn ghost" id="acc-settle">تصفية الحساب</button>' : ''}
        </div>
      </div>

      <div class="card" style="margin-top:14px">
        <h2>تفاصيل الحركات</h2>
        <p class="muted">كل حركة مسجّلة بعملتها، والرصيد الجاري محسوب لكل عملة على حدة.</p>
        ${table(['التاريخ', 'الحركة', 'المرجع', 'العملة', 'له', 'عليه', 'الرصيد', ''], stmt.entries, (e) => `
          <tr>
            <td>${esc(e.date)}</td>
            <td>${esc(e.label)}${e.note ? `<div class="muted" style="font-size:12px">${esc(e.note)}</div>` : ''}</td>
            <td>${esc(e.ref || '—')}</td>
            <td><span class="badge">${e.currency === 'USD' ? 'دولار' : 'ليرة'}</span></td>
            <td>${e.credit ? money(e.credit, e.currency) : '—'}</td>
            <td>${e.debit ? money(e.debit, e.currency) : '—'}</td>
            <td><strong>${money(e.running, e.currency)}</strong></td>
            <td>${
              e.source === 'manual'
                ? `<button class="btn small ghost" data-void="${e.id}">إلغاء</button>`
                : '<span class="badge">eganis</span>'
            }</td>
          </tr>`)}
      </div>

      <div class="card" style="margin-top:14px">
        <h2>الكشف كما سيصل العميل</h2>
        <pre id="acc-text" style="white-space:pre-wrap;font-family:inherit;font-size:13.5px;margin:0">${esc(stmt.text)}</pre>
      </div>`;

    document.getElementById('acc-copy').onclick = async () => {
      await navigator.clipboard.writeText(stmt.text).catch(() => {});
      toast('تم نسخ الكشف');
    };

    // فتح الـ PDF في تبويب جديد: من هناك يحفظه المستخدم أو يشاركه مباشرة من الجوال
    document.getElementById('acc-pdf').onclick = () => {
      const url = `/api/accounting/statement.pdf?q=${encodeURIComponent(
        state.accountingQuery,
      )}&token=${encodeURIComponent(state.token)}`;
      window.open(url, '_blank', 'noopener');
    };

    document.getElementById('acc-send-pdf').onclick = async (event) => {
      const btn = event.currentTarget;
      btn.disabled = true;
      btn.textContent = 'جارِ تجهيز الملف…';
      try {
        const result = await api('/api/accounting/send-statement', {
          method: 'POST',
          body: { q: state.accountingQuery, as: 'pdf', send: false },
        });
        state.conversationId = result.conversationId;
        toast(`تم تجهيز ${result.file.name} في محادثة العميل — أرسله من تبويب واتساب`);
      } catch (err) {
        toast(err.message, true);
      } finally {
        btn.disabled = false;
        btn.textContent = 'إرسال PDF على واتساب';
      }
    };

    document.getElementById('acc-send').onclick = async () => {
      try {
        const result = await api('/api/accounting/send-statement', {
          method: 'POST',
          body: { q: state.accountingQuery, send: false },
        });
        toast('تم تجهيز الكشف كمسوّدة في محادثة العميل على واتساب');
        state.conversationId = result.conversationId;
      } catch (err) {
        toast(err.message, true);
      }
    };

    document.getElementById('acc-add').onclick = () => openEntryForm(stmt.customer);

    const settleBtn = document.getElementById('acc-settle');
    if (settleBtn) {
      settleBtn.onclick = async () => {
        const verb = stmt.status === 'company_owes' ? 'إعادة' : 'تحصيل';
        const amounts = stmt.status === 'company_owes' ? stmt.toRefund : stmt.toCollect;
        const plain = ['TRY', 'USD']
          .filter((c) => amounts[c])
          .map((c) => `${amounts[c]} ${c === 'USD' ? '$' : '₺'}`)
          .join(' و ');
        if (!confirm(`تأكيد ${verb} مبلغ ${plain} وتصفية حساب ${stmt.customer.name}؟`)) return;
        try {
          await api('/api/accounting/settle', {
            method: 'POST',
            body: { q: state.accountingQuery, method: 'نقداً' },
          });
          toast('تمت تصفية الحساب');
          await loadStatement(state.accountingQuery);
        } catch (err) {
          toast(err.message, true);
        }
      };
    }
  }

  async function openEntryForm(customer) {
    const types = await api('/api/accounting/entry-types');
    const box = document.getElementById('acc-result');
    const form = document.createElement('div');
    form.className = 'card';
    form.style.marginTop = '14px';
    form.innerHTML = `
      <h2>إضافة حركة على حساب ${esc(customer.name)}</h2>
      <div class="field">
        <label>نوع الحركة</label>
        <select id="e-type">
          ${types
            .filter((t) => t.type !== 'settlement')
            .map((t) => `<option value="${esc(t.type)}">${esc(t.label)} — ${t.direction === 'credit' ? 'له' : 'عليه'}</option>`)
            .join('')}
        </select>
      </div>
      <div class="row" style="gap:10px;align-items:flex-end">
        <div class="field" style="flex:2"><label>المبلغ</label><input id="e-amount" type="number" min="0" step="0.01" /></div>
        <div class="field" style="flex:1">
          <label>العملة</label>
          <select id="e-currency">
            <option value="TRY">ليرة تركية ₺</option>
            <option value="USD">دولار $</option>
          </select>
        </div>
      </div>
      <p class="muted" style="margin-top:-4px">تُسجَّل الحركة بالعملة التي حدثت بها فعلاً — لا يجري أي تحويل عند الحفظ.</p>
      <div class="field"><label>المرجع (رقم عقد أو مركبة — اختياري)</label><input id="e-ref" /></div>
      <div class="field"><label>ملاحظة (اختياري)</label><input id="e-note" placeholder="مثال: إصلاح صدام أمامي بعد حادث" /></div>
      <div class="row">
        <button class="btn" id="e-save">حفظ الحركة</button>
        <button class="btn ghost" id="e-cancel">إلغاء</button>
      </div>`;
    box.appendChild(form);
    form.scrollIntoView({ behavior: 'smooth', block: 'center' });

    form.querySelector('#e-cancel').onclick = () => form.remove();
    form.querySelector('#e-save').onclick = async () => {
      const amount = Number(form.querySelector('#e-amount').value);
      if (!amount || amount <= 0) return toast('أدخل مبلغاً صحيحاً', true);
      try {
        await api('/api/accounting/entries', {
          method: 'POST',
          body: {
            customerId: customer.id,
            customerName: customer.name,
            phone: customer.phone,
            type: form.querySelector('#e-type').value,
            amount,
            currency: form.querySelector('#e-currency').value,
            ref: form.querySelector('#e-ref').value.trim() || null,
            note: form.querySelector('#e-note').value.trim() || null,
          },
        });
        toast('تمت إضافة الحركة');
        await loadStatement(state.accountingQuery);
      } catch (err) {
        toast(err.message, true);
      }
    };
  }

  document.getElementById('acc-search').onclick = () =>
    loadStatement(input.value.trim()).catch((err) => toast(err.message, true));
  input.onkeydown = (event) => {
    if (event.key === 'Enter') loadStatement(input.value.trim()).catch((err) => toast(err.message, true));
  };

  app.addEventListener('click', async (event) => {
    const row = event.target.closest('[data-open]');
    if (row) {
      input.value = row.dataset.open;
      loadStatement(row.dataset.open).catch((err) => toast(err.message, true));
      return;
    }
    const voidId = event.target.dataset?.void;
    if (voidId) {
      if (!confirm('إلغاء هذه الحركة من الحساب؟')) return;
      try {
        await api(`/api/accounting/entries/${voidId}`, { method: 'DELETE' });
        toast('تم إلغاء الحركة');
        await loadStatement(state.accountingQuery);
      } catch (err) {
        toast(err.message, true);
      }
    }
  });

  if (state.accountingQuery) await loadStatement(state.accountingQuery);
}

async function viewInbox() {
  const conversations = await api('/api/whatsapp/conversations');
  app.innerHTML = `
    <div class="toolbar">
      <button class="btn ghost" id="simulate">محاكاة رسالة واردة</button>
      <span class="muted">الردود المقترحة تُحفظ كمسوّدة ولا تُرسل إلا بضغطك.</span>
    </div>
    <div class="inbox">
      <div class="card conv-list" id="conv-list">
        ${
          conversations.length
            ? conversations
                .map(
                  (c) => `<div class="conv${c.id === state.conversationId ? ' active' : ''}" data-conv="${c.id}">
                    <strong>${esc(c.name || c.phone)} ${c.unread ? `<span class="badge new">${c.unread}</span>` : ''}</strong>
                    <small>${esc(c.last_message || '—')}</small>
                  </div>`,
                )
                .join('')
            : '<div class="empty">لا توجد محادثات</div>'
        }
      </div>
      <div class="card" id="thread-pane"><div class="empty">اختر محادثة</div></div>
    </div>`;

  document.getElementById('simulate').onclick = async () => {
    const phone = prompt('رقم العميل (مثال 970599111222):', '970599111222');
    if (!phone) return;
    const body = prompt('نص رسالة العميل:', 'مرحبا، بدي أمدد العقد يومين');
    if (!body) return;
    try {
      const result = await api('/api/whatsapp/simulate', { method: 'POST', body: { phone, body } });
      state.conversationId = result.conversationId;
      toast(result.draft ? 'وصلت الرسالة وتم اقتراح رد' : 'وصلت الرسالة (تعذّر اقتراح رد)');
      render();
    } catch (err) {
      toast(err.message, true);
    }
  };

  document.getElementById('conv-list').onclick = (event) => {
    const item = event.target.closest('[data-conv]');
    if (!item) return;
    state.conversationId = Number(item.dataset.conv);
    render();
  };

  if (state.conversationId) await renderThread(state.conversationId);
}

async function renderThread(id) {
  const pane = document.getElementById('thread-pane');
  const { conversation, messages } = await api(`/api/whatsapp/conversations/${id}`);
  pane.innerHTML = `
    <h2>${esc(conversation.name || conversation.phone)} <span class="badge ${esc(conversation.status)}">${esc(label(conversation.status))}</span></h2>
    <div class="thread" id="thread">
      ${messages
        .map(
          (m) => `<div class="msg ${m.direction}">${esc(m.body)}
            <span class="meta">${esc(label(m.status))} · ${fmtDate(m.created_at)}${m.author === 'ai' ? ' · مقترح آلي' : ''}</span>
          </div>`,
        )
        .join('')}
    </div>
    <div class="field" style="margin-top:12px">
      <label>الرد</label>
      <textarea id="reply-box">${esc(
        [...messages].reverse().find((m) => m.status === 'draft')?.body || '',
      )}</textarea>
    </div>
    <div class="row">
      <button class="btn" id="send-btn">إرسال</button>
      <button class="btn ghost" id="draft-btn">اقترح رداً</button>
      <button class="btn ghost" id="save-template-btn">احفظ كرد مدرَّب</button>
      <button class="btn ghost" id="close-conv-btn">إغلاق المحادثة</button>
    </div>`;

  const thread = document.getElementById('thread');
  thread.scrollTop = thread.scrollHeight;
  const box = document.getElementById('reply-box');

  document.getElementById('draft-btn').onclick = async () => {
    try {
      toast('جارِ صياغة الرد…');
      const { draft } = await api(`/api/whatsapp/conversations/${id}/draft`, { method: 'POST' });
      box.value = draft.reply;
      toast(
        `اقتراح جاهز (${draft.intent}) — الثقة ${Math.round(draft.confidence * 100)}%${
          draft.requires_human ? ' · يحتاج مراجعة موظف' : ''
        }`,
      );
    } catch (err) {
      toast(err.message, true);
    }
  };

  document.getElementById('send-btn').onclick = async () => {
    if (!box.value.trim()) return toast('اكتب نص الرسالة أولاً', true);
    try {
      await api(`/api/whatsapp/conversations/${id}/send`, {
        method: 'POST',
        body: { body: box.value },
      });
      toast('تم إرسال الرسالة');
      await renderThread(id);
    } catch (err) {
      toast(err.message, true);
    }
  };

  document.getElementById('save-template-btn').onclick = async () => {
    const intent = prompt('موضوع هذا الرد (مثال: تمديد عقد):', '');
    if (!intent) return;
    const lastIn = [...messages].reverse().find((m) => m.direction === 'in');
    try {
      await api('/api/templates', {
        method: 'POST',
        body: { intent, sampleIn: lastIn?.body || null, reply: box.value },
      });
      toast('تم حفظ الرد ضمن الردود المدرَّبة');
    } catch (err) {
      toast(err.message, true);
    }
  };

  document.getElementById('close-conv-btn').onclick = async () => {
    try {
      await api(`/api/whatsapp/conversations/${id}/status`, {
        method: 'POST',
        body: { status: 'closed' },
      });
      toast('تم إغلاق المحادثة');
      render();
    } catch (err) {
      toast(err.message, true);
    }
  };
}

async function viewTemplates() {
  const templates = await api('/api/templates');
  app.innerHTML = `
    <div class="grid two">
      <div class="card">
        <h2>إضافة رد مدرَّب</h2>
        <div class="field"><label>الموضوع</label><input id="t-intent" placeholder="استفسار سعر" /></div>
        <div class="field"><label>رسالة عميل نموذجية (اختياري)</label><input id="t-sample" placeholder="كم سعر السيارة باليوم؟" /></div>
        <div class="field"><label>الرد المعتمد</label><textarea id="t-reply"></textarea></div>
        <div class="field"><label>ملاحظات (اختياري)</label><input id="t-notes" /></div>
        <button class="btn" id="t-save">حفظ</button>
      </div>
      <div class="card">
        <h2>الردود المحفوظة (${templates.length})</h2>
        <p class="muted">هذه الردود هي أسلوب الشركة الذي يتعلّم منه النظام عند صياغة أي رد جديد.</p>
        ${table(['الموضوع', 'الرد', 'الاستخدام', ''], templates, (t) => `
          <tr>
            <td>${esc(t.intent)}</td>
            <td>${esc(t.reply.slice(0, 90))}${t.reply.length > 90 ? '…' : ''}</td>
            <td>${t.used_count}</td>
            <td><button class="btn small danger" data-del="${t.id}">حذف</button></td>
          </tr>`)}
      </div>
    </div>`;

  document.getElementById('t-save').onclick = async () => {
    const payload = {
      intent: document.getElementById('t-intent').value.trim(),
      sampleIn: document.getElementById('t-sample').value.trim(),
      reply: document.getElementById('t-reply').value.trim(),
      notes: document.getElementById('t-notes').value.trim(),
    };
    if (!payload.intent || !payload.reply) return toast('الموضوع والرد مطلوبان', true);
    try {
      await api('/api/templates', { method: 'POST', body: payload });
      toast('تمت الإضافة');
      render();
    } catch (err) {
      toast(err.message, true);
    }
  };

  app.addEventListener('click', async (event) => {
    const id = event.target.dataset?.del;
    if (!id) return;
    try {
      await api(`/api/templates/${id}`, { method: 'DELETE' });
      toast('تم الحذف');
      render();
    } catch (err) {
      toast(err.message, true);
    }
  });
}

async function viewAudit() {
  const rows = await api('/api/audit?limit=150');
  app.innerHTML = `<div class="card">
    <h2>سجل الأوامر</h2>
    <p class="muted">كل أمر تعديل أو رسالة مُرسلة يُسجَّل هنا مع منفّذه ووقته.</p>
    ${table(['الوقت', 'المنفّذ', 'الأمر', 'الهدف', 'النتيجة'], rows, (r) => `
      <tr>
        <td>${fmtDate(r.created_at)}</td><td>${esc(r.actor)}</td><td>${esc(r.action)}</td>
        <td>${esc(r.target || '—')}</td>
        <td>${r.ok ? '<span class="badge open">نجح</span>' : `<span class="badge overdue">فشل</span>`}</td>
      </tr>`)}
  </div>`;
}

// ===== التوجيه =====

// ===== الإعدادات: ربط eganis من داخل التطبيق =====

async function viewSettings() {
  const s = await api('/api/settings');
  const f = s.fields;

  app.innerHTML = `
    <div class="card">
      <h2>ربط eganis</h2>
      <p class="muted">
        اكتب بيانات دخولك للوحة eganis هنا ويقرأ التطبيق منها مباشرة.
        البيانات تُحفظ في خادمك أنت ولا تغادره.
      </p>

      <div class="field">
        <label>وضع الربط</label>
        <select id="set-driver">
          <option value="mock" ${f.eganisDriver.value === 'mock' ? 'selected' : ''}>تجريبي — بيانات وهمية للتجربة</option>
          <option value="browser" ${['browser', 'http'].includes(f.eganisDriver.value) ? 'selected' : ''}>بحسابك في اللوحة — الوضع الموصى به</option>
          <option value="api" ${f.eganisDriver.value === 'api' ? 'selected' : ''}>عبر API — إن وفّره مزوّد البرنامج</option>
          <option value="browser-full" ${f.eganisDriver.value === 'browser-full' ? 'selected' : ''}>متصفّح كامل — للوحات تُبنى بجافاسكربت (يحتاج ذاكرة كبيرة)</option>
        </select>
      </div>

      <div class="field">
        <label>رابط لوحة eganis</label>
        <input id="set-url" inputmode="url" placeholder="https://panel.eganis.com.tr"
               value="${esc(f.eganisBaseUrl.value)}" />
      </div>

      <div class="field">
        <label>اسم المستخدم</label>
        <input id="set-user" autocomplete="off" value="${esc(f.eganisUsername.value)}" />
      </div>

      <div class="field">
        <label>كلمة السر ${f.eganisPassword.set ? '<span class="badge open">محفوظة</span>' : ''}</label>
        <input id="set-pass" type="password" autocomplete="new-password"
               placeholder="${f.eganisPassword.set ? 'اتركها فارغة إن لم ترد تغييرها' : ''}" />
      </div>

      <div class="row">
        <button class="btn" id="set-save">حفظ واختبار الربط</button>
        <button class="btn ghost" id="set-diag">لماذا فشل الدخول؟</button>
        <button class="btn ghost" id="set-shot">اعرض ما يراه الخادم</button>
      </div>

      <div id="set-result" style="margin-top:12px"></div>
    </div>

    <div class="card" style="margin-top:14px" id="pages-card">
      <h2>صفحات لوحتك</h2>
      <p class="muted">
        الاكتشاف التلقائي يفتح صفحات لوحتك ويتعرّف على كل واحدة من أعمدة جدولها
        (لا من اسمها)، ويحفظ النتيجة. يستغرق دقيقة أو اثنتين مرة واحدة فقط.
      </p>
      <div class="row">
        <button class="btn" id="pages-auto">اكتشف صفحاتي تلقائياً</button>
        <button class="btn ghost" id="pages-load">أو اخترها بنفسي</button>
      </div>
      <div id="pages-box" style="margin-top:12px"></div>
    </div>

    <div class="card" style="margin-top:14px">
      <h2>سعر الصرف</h2>
      <div class="field">
        <label>المصدر</label>
        <select id="set-fx">
          <option value="harem" ${f.fxSource.value === 'harem' ? 'selected' : ''}>حرم ألتين — سعر السوق</option>
          <option value="tcmb" ${f.fxSource.value === 'tcmb' ? 'selected' : ''}>البنك المركزي التركي</option>
          <option value="erapi" ${f.fxSource.value === 'erapi' ? 'selected' : ''}>مصدر احتياطي</option>
        </select>
      </div>
      <div class="field">
        <label>سعر الشركة الاحتياطي (كم ليرة للدولار)</label>
        <input id="set-rate" type="number" step="0.01" value="${esc(f.fxManualRate.value)}" />
      </div>
      <div class="row"><button class="btn ghost" id="set-save-fx">حفظ</button></div>
    </div>

    ${
      s.envLines.length || s.hasStoredSecrets
        ? `<div class="card" style="margin-top:14px">
             <h2>تثبيت الإعدادات على الاستضافة</h2>
             <p class="muted">${esc(s.note)}</p>
             <pre style="white-space:pre-wrap;font-size:13px;margin:0;direction:ltr;text-align:left">${esc(
               [...s.envLines, ...(s.hasStoredSecrets ? ['EGANIS_PASSWORD=«كلمة السر التي أدخلتها»'] : [])].join('\n'),
             )}</pre>
           </div>`
        : ''
    }`;

  const box = document.getElementById('set-result');

  async function saveAndTest() {
    box.innerHTML = '<div class="empty">جارِ الحفظ والاختبار… قد يستغرق نصف دقيقة</div>';
    try {
      await api('/api/settings', {
        method: 'POST',
        body: {
          eganisDriver: document.getElementById('set-driver').value,
          eganisBaseUrl: document.getElementById('set-url').value,
          eganisUsername: document.getElementById('set-user').value,
          eganisPassword: document.getElementById('set-pass').value,
        },
      });

      const result = await api('/api/settings/test', { method: 'POST' });
      if (!result.ok) {
        box.innerHTML = `<div class="alert high">تعذّر الاتصال: ${esc(result.error || 'سبب غير معروف')}</div>
          <p class="muted">اضغط «لماذا فشل الدخول؟» ليقرأ الخادم نموذج لوحتك ويقول ما ينقصه.</p>`;
        return;
      }

      const pages = (result.pages || []).join('، ') || '—';
      // القراءة قد تفشل لصفحة بعينها فيصلنا كائن خطأ لا رقم
      const count = (value) =>
        typeof value === 'number' ? String(value) : value?.error ? `تعذّرت — ${value.error}` : '—';
      const missing = ['contracts', 'vehicles'].filter((k) => !(result.pages || []).includes(k));

      box.innerHTML = `
        <div class="alert" style="background:rgba(23,121,74,.14);color:var(--ok)">
          تم تسجيل الدخول بنجاح ✔
        </div>
        <div class="kv-list">
          <div><span class="muted">الصفحات المكتشفة:</span> ${esc(pages)}</div>
          <div><span class="muted">العقود المقروءة:</span> ${esc(count(result.sample?.contracts))}</div>
          <div><span class="muted">المركبات المقروءة:</span> ${esc(count(result.sample?.vehicles))}</div>
        </div>
        ${
          result.sample?.firstContract
            ? `<p class="muted" style="margin-top:8px">أول عقد: ${esc(
                result.sample.firstContract.no || '',
              )} — ${esc(result.sample.firstContract.customerName || '')}</p>`
            : ''
        }
        ${
          missing.length
            ? `<div class="alert medium" style="margin-top:10px">
                 لم أتعرّف على صفحات لوحتك من أسمائها — اضغط «اكتشف صفحاتي تلقائياً» أدناه.
               </div>`
            : '<p class="muted">افتح «لوحة اليوم» لترى بياناتك.</p>'
        }`;
      // لا نفتح شيئاً تلقائياً: الاكتشاف التلقائي بضغطة واحدة أدناه
      toast(missing.length ? 'الدخول نجح — بقي تحديد الصفحات' : 'تم ربط eganis بنجاح');
    } catch (err) {
      box.innerHTML = `<div class="alert high">${esc(err.message)}</div>`;
    }
  }

  const PAGE_KINDS = [
    ['contracts', 'العقود'],
    ['vehicles', 'المركبات'],
    ['bookings', 'الحجوزات'],
    ['customers', 'العملاء'],
    ['ledger', 'حسابات العملاء (Cari Hesap)'],
  ];

  async function loadLinks() {
    const pagesBox = document.getElementById('pages-box');
    pagesBox.innerHTML = '<div class="empty">جارِ قراءة قائمة لوحتك…</div>';
    try {
      const { links } = await api('/api/eganis/links');
      if (!links.length) {
        pagesBox.innerHTML = '<div class="alert medium">لم أجد روابط في اللوحة — أرسل لي لقطة «اعرض ما يراه الخادم».</div>';
        return;
      }

      let chosen = {};
      try {
        chosen = JSON.parse(f.eganisPages.value || '{}');
      } catch {
        chosen = {};
      }

      const options = (kind) =>
        [
          '<option value="">— لا شيء —</option>',
          ...links.map(
            (l) =>
              `<option value="${esc(l.href)}" ${chosen[kind] === l.href ? 'selected' : ''}>${esc(
                l.text || l.href,
              )}${l.guess === kind ? ' ✓' : ''}</option>`,
          ),
        ].join('');

      pagesBox.innerHTML = `
        ${PAGE_KINDS.map(
          ([kind, label]) => `
          <div class="field">
            <label>${label}</label>
            <select data-kind="${kind}">${options(kind)}</select>
          </div>`,
        ).join('')}
        <div class="row"><button class="btn" id="pages-save">حفظ الصفحات واختبار القراءة</button></div>
        <p class="muted">وجدت ${links.length} رابطاً في لوحتك.</p>`;

      document.getElementById('pages-save').onclick = async () => {
        const map = {};
        pagesBox.querySelectorAll('select[data-kind]').forEach((el) => {
          if (el.value) map[el.dataset.kind] = el.value;
        });
        try {
          await api('/api/settings', { method: 'POST', body: { eganisPages: JSON.stringify(map) } });
          toast('تم حفظ الصفحات — جارِ الاختبار');
          await saveAndTest();
        } catch (err) {
          toast(err.message, true);
        }
      };
    } catch (err) {
      pagesBox.innerHTML = `<div class="alert high">${esc(err.message)}</div>`;
    }
  }

  async function autodetect() {
    const pagesBox = document.getElementById('pages-box');
    const btn = document.getElementById('pages-auto');
    btn.disabled = true;
    pagesBox.innerHTML = '<div class="empty">جارِ فتح لوحتك…</div>';

    const KIND_LABEL = {
      contracts: 'العقود',
      vehicles: 'المركبات',
      bookings: 'الحجوزات',
      customers: 'العملاء',
      ledger: 'حسابات العملاء',
    };

    try {
      await api('/api/eganis/autodetect', { method: 'POST' });

      // نتابع التقدّم حتى ينتهي الفحص
      for (let tick = 0; tick < 200; tick += 1) {
        await new Promise((resolve) => setTimeout(resolve, 3000));
        const state = await api('/api/eganis/autodetect');

        if (state.running) {
          const p = state.progress || {};
          pagesBox.innerHTML = `<div class="empty">جارِ فحص صفحات لوحتك…<br>
            ${p.total ? `${p.index} من ${p.total}` : ''} ${esc(p.text || '')}</div>`;
          continue;
        }

        if (state.error) {
          pagesBox.innerHTML = `<div class="alert high">${esc(state.error)}</div>`;
          break;
        }

        if (state.result) {
          const found = state.result.found || {};
          const rows = Object.entries(found);
          pagesBox.innerHTML = rows.length
            ? `<div class="alert" style="background:rgba(23,121,74,.14);color:var(--ok)">
                 وجدت ${rows.length} صفحة من أصل ${state.result.scanned} صفحة فحصتها
               </div>
               <div class="kv-list">
                 ${rows
                   .map(
                     ([kind, v]) =>
                       `<div><span class="muted">${esc(KIND_LABEL[kind] || kind)}:</span>
                        ${esc(v.text || v.href)} <span class="muted">(${v.rows} صف)</span></div>`,
                   )
                   .join('')}
               </div>`
            : `<div class="alert medium">لم أتعرّف على أي صفحة — اضغط «أو اخترها بنفسي».</div>`;
          if (rows.length) await saveAndTest();
          break;
        }
      }
    } catch (err) {
      pagesBox.innerHTML = `<div class="alert high">${esc(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  }

  document.getElementById('pages-auto').onclick = autodetect;
  document.getElementById('pages-load').onclick = loadLinks;
  document.getElementById('set-save').onclick = saveAndTest;

  /*
   * تشخيص الدخول داخل التطبيق لا عبر فتح رابط: الواجهة تحمل رمز الدخول،
   * وصاحب الشركة يعمل من جواله فلا يُطلب منه نسخ سجلّات الاستضافة.
   */
  document.getElementById('set-diag').onclick = async (event) => {
    const btn = event.currentTarget;
    btn.disabled = true;
    box.innerHTML = '<p class="muted">أفحص نموذج الدخول في لوحتك…</p>';
    try {
      const d = await api('/api/eganis/login-check');
      if (d.ok) {
        box.innerHTML = `<div class="alert" style="background:rgba(23,121,74,.14);color:var(--ok)">
          الدخول ناجح ✔ ${esc(d.title || '')}</div>`;
        return;
      }

      const line = (label, value) =>
        `<tr><td class="muted" style="padding:4px 10px 4px 0;white-space:nowrap">${label}</td>
             <td style="padding:4px 0"><code>${esc(String(value ?? '—'))}</code></td></tr>`;

      const report = [
        `السبب: ${d.error || '—'}`,
        `الرابط: ${d.url || '—'}`,
        `المستخدم: ${d.user || '—'} (${d.userShape || '—'})`,
        `كلمة السر: ${d.passwordLength ?? 0} حرفاً (${d.passwordShape || '—'})`,
        `عنوان الصفحة: ${d.title || '—'}`,
        d.summary || '',
      ].join('\n');

      box.innerHTML = `
        <div class="alert high">${esc(d.error || 'فشل الدخول')}</div>
        <table style="width:100%;font-size:13px;margin-top:8px">
          ${line('الرابط', d.url)}
          ${line('المستخدم', `${d.user} — ${d.userShape}`)}
          ${line('كلمة السر', `${d.passwordLength} حرفاً — ${d.passwordShape}`)}
          ${line('عنوان الصفحة', d.title)}
        </table>
        <p class="muted" style="margin-top:10px">ما يطلبه نموذج لوحتك فعلاً:</p>
        <pre style="white-space:pre-wrap;word-break:break-word;font-size:12px;
             background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px"
          >${esc(d.summary || '—')}</pre>
        <button class="btn ghost" id="diag-copy">انسخ التقرير</button>`;

      document.getElementById('diag-copy').onclick = async () => {
        try {
          await navigator.clipboard.writeText(report);
          toast('تم نسخ التقرير');
        } catch {
          toast('تعذّر النسخ — حدّد النص يدوياً', true);
        }
      };
    } catch (err) {
      box.innerHTML = `<div class="alert high">${esc(err.message)}</div>`;
    } finally {
      btn.disabled = false;
    }
  };

  document.getElementById('set-shot').onclick = async () => {
    const url = `/api/eganis/screenshot?token=${encodeURIComponent(state.token)}&t=${Date.now()}`;
    box.innerHTML = '<p class="muted">ألتقط صورة لما يراه الخادم…</p>';
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${state.token}` } });
      // وضع القراءة الخفيفة بلا متصفّح فلا صورة — نقول ذلك بدل صورة مكسورة
      if (!res.ok || !(res.headers.get('content-type') || '').startsWith('image/')) {
        const data = await res.json().catch(() => ({}));
        box.innerHTML = `<div class="alert medium">${esc(data.error || 'الصورة غير متاحة')}</div>
          <p class="muted">استخدم «لماذا فشل الدخول؟» — يقرأ نموذج لوحتك ويصفه نصّاً.</p>`;
        return;
      }
      const blob = URL.createObjectURL(await res.blob());
      box.innerHTML = `<p class="muted">هذا ما يفتحه الخادم داخل لوحة eganis الآن:</p>
        <img src="${blob}" alt="لقطة لوحة eganis"
             style="width:100%;border:1px solid var(--border);border-radius:10px" />`;
    } catch (err) {
      box.innerHTML = `<div class="alert high">${esc(err.message)}</div>`;
    }
  };

  document.getElementById('set-save-fx').onclick = async () => {
    try {
      await api('/api/settings', {
        method: 'POST',
        body: {
          fxSource: document.getElementById('set-fx').value,
          fxManualRate: document.getElementById('set-rate').value,
        },
      });
      toast('تم حفظ إعدادات سعر الصرف');
    } catch (err) {
      toast(err.message, true);
    }
  };
}

const views = {
  today: viewToday,
  settings: viewSettings,
  assistant: viewAssistant,
  contracts: viewContracts,
  fleet: viewFleet,
  accounting: viewAccounting,
  inbox: viewInbox,
  templates: viewTemplates,
  audit: viewAudit,
};

async function render() {
  app.innerHTML = '<div class="empty">جارِ التحميل…</div>';
  try {
    await views[state.view]();
    state.lastRender = Date.now();
  } catch (err) {
    app.innerHTML = `<div class="card"><h2>تعذّر التحميل</h2><p class="muted">${esc(err.message)}</p></div>`;
    toast(err.message, true);
  }
}

/**
 * تحديث تلقائي: أي تعديل تعمله على eganis يظهر هنا بلا ضغط تحديث.
 * يقتصر على الشاشات التي تعرض بيانات فقط — لا نُعيد بناء شاشة فيها نموذج
 * أو رسالة نصف مكتوبة.
 */
const LIVE_VIEWS = ['today', 'contracts', 'fleet'];
const LIVE_EVERY_MS = 30000;

setInterval(async () => {
  if (!LIVE_VIEWS.includes(state.view)) return;
  if (document.hidden) return; // التطبيق في الخلفية — لا داعي
  if (document.activeElement?.matches('input, select, textarea')) return;
  if (Date.now() - (state.lastRender || 0) < LIVE_EVERY_MS - 1000) return;

  try {
    await views[state.view]();
    state.lastRender = Date.now();
  } catch {
    /* انقطاع مؤقت — نحاول في الدورة التالية بلا إزعاج */
  }
}, LIVE_EVERY_MS);

// عند العودة للتطبيق من الخلفية: حدّث فوراً بدل انتظار الدورة
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && LIVE_VIEWS.includes(state.view)) render();
});

async function refreshStatus() {
  try {
    const status = await api('/api/system/status');
    const eganisOk = status.connectors.eganis.ok;
    statusPill.textContent = `eganis: ${status.connectors.eganis.driver}${eganisOk ? ' ✓' : ' ✗'} · واتساب: ${status.connectors.whatsapp.driver} · ذكاء: ${status.app.aiConfigured ? 'مفعّل' : 'غير مهيّأ'}`;
    statusPill.className = `pill ${eganisOk ? 'ok' : 'bad'}`;
  } catch (err) {
    statusPill.textContent = 'غير متصل — تحقق من رمز الدخول';
    statusPill.className = 'pill bad';
  }
}

document.getElementById('tabs').onclick = (event) => {
  const tab = event.target.closest('.tab');
  if (!tab) return;
  document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t === tab));
  state.view = tab.dataset.view;
  render();
};

document.getElementById('refresh-btn').onclick = () => {
  refreshStatus();
  render();
};

document.getElementById('token-btn').onclick = () => {
  const token = prompt('رمز الدخول (APP_TOKEN):', state.token);
  if (token === null) return;
  state.token = token.trim();
  localStorage.setItem('appToken', state.token);
  refreshStatus();
  render();
};

// تسجيل عامل الخدمة ليعمل التطبيق كأيقونة على شاشة الموبايل
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js').catch(() => {});
}

refreshStatus();
render();
setInterval(refreshStatus, 60000);
