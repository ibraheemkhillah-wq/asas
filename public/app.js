const app = document.getElementById('app');
const toastEl = document.getElementById('toast');
const statusPill = document.getElementById('status-pill');

const state = {
  view: 'today',
  token: localStorage.getItem('appToken') || '',
  conversationId: null,
  accountingQuery: '',
  accountingCustomer: null,
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

const money = (n) =>
  `<bdi dir="ltr">${Number(n || 0).toLocaleString('ar-EG')} ₺</bdi>`;

const fmtDate = (value) =>
  value
    ? new Date(value).toLocaleString('ar-EG', {
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
      ${kpi(money(c.unpaidBalance), 'رصيد غير محصّل', c.unpaidBalance ? 'warn' : 'ok')}
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
            <td>${fmtDate(r.endAt)}</td><td>${money(r.balance)}</td>
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
          <td>${badge(r.status)}</td><td>${money(r.balance)}</td>
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

// ===== محاسبة المستأجرين =====

async function viewAccounting() {
  const balances = await api('/api/accounting/open-balances');

  app.innerHTML = `
    <div class="toolbar">
      <input id="acc-q" placeholder="اكتب اسم العميل أو رقم هاتفه…" value="${esc(state.accountingQuery || '')}" />
      <button class="btn" id="acc-search">عرض الحساب</button>
    </div>
    <div id="acc-result"></div>
    <div class="card" style="margin-top:14px">
      <h2>حسابات غير مصفّاة</h2>
      <p class="muted">العملاء الذين لهم رصيد عندنا أو عليهم مستحقات — اضغط أي اسم لفتح كشفه.</p>
      ${table(['العميل', 'الهاتف', 'تأمينات محفوظة', 'الحالة', 'المبلغ'], balances, (b) => `
        <tr class="clickable" data-open="${esc(b.customer.name)}">
          <td>${esc(b.customer.name)}</td>
          <td>${esc(b.customer.phone || '—')}</td>
          <td>${money(b.depositsHeld)}</td>
          <td>${
            b.status === 'company_owes'
              ? '<span class="badge open">له عندنا</span>'
              : '<span class="badge overdue">مطلوب منه</span>'
          }</td>
          <td><strong>${money(b.status === 'company_owes' ? b.toRefund : b.toCollect)}</strong></td>
        </tr>`)}
    </div>`;

  const input = document.getElementById('acc-q');

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
          : { text: 'الحساب مصفّى', value: 0, cls: '' };

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
            <div class="kpi-value ${headline.cls}">${money(headline.value)}</div>
            <div class="kpi-label">${esc(headline.text)}</div>
          </div>
        </div>

        <div class="grid kpi" style="margin-top:14px">
          <div class="card"><div class="kpi-value">${money(stmt.totals.depositsHeld)}</div><div class="kpi-label">تأمينات محفوظة</div></div>
          <div class="card"><div class="kpi-value">${money(stmt.totals.credits)}</div><div class="kpi-label">إجمالي ما دفعه</div></div>
          <div class="card"><div class="kpi-value">${money(stmt.totals.debits)}</div><div class="kpi-label">إجمالي المستحقات عليه</div></div>
          <div class="card"><div class="kpi-value ${stmt.totals.damages ? 'warn' : ''}">${money(stmt.totals.damages)}</div><div class="kpi-label">تكاليف حوادث</div></div>
        </div>

        <div class="row" style="margin-top:14px">
          <button class="btn" id="acc-send">إرسال الكشف للعميل</button>
          <button class="btn ghost" id="acc-copy">نسخ الكشف</button>
          <button class="btn ghost" id="acc-add">إضافة حركة</button>
          ${stmt.status !== 'settled' ? '<button class="btn ghost" id="acc-settle">تصفية الحساب</button>' : ''}
        </div>
      </div>

      <div class="card" style="margin-top:14px">
        <h2>تفاصيل الحركات</h2>
        ${table(['التاريخ', 'الحركة', 'المرجع', 'له', 'عليه', 'الرصيد', ''], stmt.entries, (e) => `
          <tr>
            <td>${esc(e.date)}</td>
            <td>${esc(e.label)}${e.note ? `<div class="muted" style="font-size:12px">${esc(e.note)}</div>` : ''}</td>
            <td>${esc(e.ref || '—')}</td>
            <td>${e.credit ? money(e.credit) : '—'}</td>
            <td>${e.debit ? money(e.debit) : '—'}</td>
            <td><strong>${money(e.running)}</strong></td>
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
        const amount = stmt.status === 'company_owes' ? stmt.toRefund : stmt.toCollect;
        if (!confirm(`تأكيد ${verb} مبلغ ${amount} ₺ وتصفية حساب ${stmt.customer.name}؟`)) return;
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
      <div class="field"><label>المبلغ (₺)</label><input id="e-amount" type="number" min="0" step="0.01" /></div>
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

const views = {
  today: viewToday,
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
  } catch (err) {
    app.innerHTML = `<div class="card"><h2>تعذّر التحميل</h2><p class="muted">${esc(err.message)}</p></div>`;
    toast(err.message, true);
  }
}

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
