import test from 'node:test';
import assert from 'node:assert/strict';
import * as html from '../src/connectors/eganis/html.js';

test('نصّ الخلية يخرج نظيفاً من الوسوم والرموز', () => {
  assert.equal(html.textOf('<td><b>Ahmet</b>&nbsp;Nassar</td>'), 'Ahmet Nassar');
  assert.equal(html.textOf('<span>34&nbsp;ABC&nbsp;123</span>'), '34 ABC 123');
  assert.equal(html.textOf('<td>A<br>B</td>'), 'A B');
  assert.equal(html.textOf('<td>Sözleşme &amp; Fatura</td>'), 'Sözleşme & Fatura');
  assert.equal(html.textOf('<script>var x = "<td>";</script>Metin'), 'Metin');
});

test('رموز HTML العددية تُفكّ', () => {
  assert.equal(html.decodeEntities('&#214;deme'), 'Ödeme');
  assert.equal(html.decodeEntities('&#x15E;ube'), 'Şube');
});

test('جدول تركي عادي يُقرأ ترويسةً وصفوفاً', () => {
  const page = `<table><thead><tr><th>Plaka</th><th>Marka</th><th>Durum</th></tr></thead>
    <tbody>
      <tr><td>34 ABC 123</td><td>Hyundai</td><td>Kirada</td></tr>
      <tr><td>34 XYZ 789</td><td>Fiat</td><td>Açık</td></tr>
    </tbody></table>`;
  const [t] = html.extractTables(page);
  assert.deepEqual(t.headers, ['Plaka', 'Marka', 'Durum']);
  assert.equal(t.rows.length, 2);
  assert.deepEqual(t.rows[0], ['34 ABC 123', 'Hyundai', 'Kirada']);
});

test('جدول بلا thead: الصفّ الأول ترويسة', () => {
  const page = '<table><tr><th>Ad</th><th>Telefon</th></tr><tr><td>Leyla</td><td>0544</td></tr></table>';
  const [t] = html.extractTables(page);
  assert.deepEqual(t.headers, ['Ad', 'Telefon']);
  assert.deepEqual(t.rows, [['Leyla', '0544']]);
});

test('جدول داخل جدول لا يخلط صفوفه بالحاوي', () => {
  const page = `<table><thead><tr><th>Dış</th></tr></thead><tbody>
    <tr><td><table><thead><tr><th>İç</th></tr></thead><tbody><tr><td>x</td></tr></tbody></table></td></tr>
    </tbody></table>`;
  const tables = html.extractTables(page);
  assert.equal(tables.length, 2);
  const outer = tables.find((t) => t.headers[0] === 'Dış');
  const inner = tables.find((t) => t.headers[0] === 'İç');
  assert.ok(outer && inner);
  // الحاوي أسقط الجدول الداخلي فلم يبقَ له صفّ بيانات
  assert.equal(outer.rows.length, 0);
  assert.deepEqual(inner.rows, [['x']]);
});

test('خلايا بلا وسوم إغلاق تُقرأ أيضاً', () => {
  const page = '<table><tr><th>A<th>B<tr><td>1<td>2</table>';
  const [t] = html.extractTables(page);
  assert.deepEqual(t.headers, ['A', 'B']);
  assert.deepEqual(t.rows, [['1', '2']]);
});

test('روابط اللوحة تُلتقط ويُستبعد ما ليس تنقّلاً', () => {
  const page = `<a href="/sozlesmeler">İşlemler</a>
    <a href="#">Boş</a><a href="javascript:void(0)">JS</a><a href="mailto:a@b.c">Mail</a>`;
  const links = html.extractLinks(page);
  assert.equal(links.length, 1);
  assert.deepEqual(links[0], { text: 'İşlemler', href: '/sozlesmeler' });
});

test('نموذج الدخول يُقرأ بحقوله المخفية', () => {
  const page = `<header><input type="text" name="q"></header>
    <form method="post" action="/Account/Login">
      <input type="hidden" name="__RequestVerificationToken" value="tok123">
      <label for="Email">E-posta</label>
      <input type="text" id="Email" name="Email" required>
      <input type="password" name="Sifre" required>
      <input type="checkbox" name="BeniHatirla" value="true">
      <button type="submit">Giriş Yap</button>
    </form>`;
  const form = html.findLoginForm(page);
  assert.equal(form.action, '/Account/Login');
  assert.equal(form.method, 'POST');

  const token = form.fields.find((f) => f.name === '__RequestVerificationToken');
  assert.equal(token.value, 'tok123');
  assert.equal(token.type, 'hidden');

  // مربّع البحث خارج النموذج فلا يدخل في حقوله
  assert.equal(form.fields.some((f) => f.name === 'q'), false);
  assert.equal(form.fields.find((f) => f.name === 'Email').required, true);
  assert.deepEqual(form.labels[0], { forId: 'Email', text: 'E-posta' });
});

test('كشف صفحة الدخول برؤية حقل كلمة السر', () => {
  assert.equal(html.looksLikeLogin('<input type="password" name="p">'), true);
  assert.equal(html.looksLikeLogin('<table><tr><td>veri</td></tr></table>'), false);
});

test('رسالة رفض اللوحة تُستخرج من حاويتها', () => {
  const page = '<div class="validation-summary-errors"><ul><li>Kullanıcı adı veya şifre hatalı.</li></ul></div>';
  assert.ok(html.extractErrors(page).includes('Kullanıcı adı veya şifre hatalı.'));
});

test('رسالة رفض بلا حاوية معروفة تُلتقط بالكلمات', () => {
  const page = '<div class="mesaj"><span>Bu alan zorunludur.</span></div>';
  assert.ok(html.extractErrors(page).some((m) => m.includes('zorunludur')));
});

test('كشف لوحة تعالج كلمة السر بجافاسكربت', () => {
  const page = `<form id="f" onsubmit="return prepare()">
      <input type="text" name="UserName"><input type="password" id="Password" name="Password">
    </form>
    <script src="/lib/md5.min.js"></script>
    <script>function prepare(){ document.getElementById('Password').value = CryptoJS.MD5(x); }</script>`;
  const form = html.findLoginForm(page);
  const scripts = html.analyzeLoginScripts(page, form);
  assert.equal(scripts.touchesPassword, true);
  assert.equal(scripts.submitHandler, true);
  assert.ok(scripts.cryptoHints.length > 0);
  assert.equal(scripts.needsBrowser, true);
});

test('لوحة عادية لا تُصنَّف كمحتاجة متصفّحاً', () => {
  const page = `<form method="post" action="/Account/Login">
      <input type="text" name="UserName"><input type="password" name="Password">
      <button type="submit">Giriş</button>
    </form>
    <script src="/lib/bootstrap.min.js"></script>`;
  const scripts = html.analyzeLoginScripts(page, html.findLoginForm(page));
  assert.equal(scripts.needsBrowser, false);
});

test('كابتشا تُعدّ سبباً كافياً للمتصفّح', () => {
  const page = '<form><input type="password" name="p"></form><div class="g-recaptcha"></div>';
  assert.equal(html.analyzeLoginScripts(page, html.findLoginForm(page)).needsBrowser, true);
});
