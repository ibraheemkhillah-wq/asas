import test from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import crypto from 'node:crypto';

/*
 * لوحة ASP.NET مصغّرة داخل الاختبار: رمز مضاد للتزوير مقترن بين الكوكي
 * والحقل، وحقول UserName/Password/RememberMe، وجداول تركية. تُشغَّل في
 * العملية نفسها فلا تحتاج شبكة ولا متصفّحاً.
 */
const USER = 'Ibrahimkhllla@callrent.net';
const PASS = 'Dogru#2026';

const TABLES = {
  Sozlesme: {
    headers: ['Sözleşme No', 'Müşteri', 'Telefon', 'Plaka', 'Başlangıç', 'Bitiş', 'Durum',
      'Günlük', 'Toplam', 'Ödenen', 'Bakiye', 'Depozito', 'Para Birimi'],
    rows: [
      ['CR-2041', 'Ahmet Nassar', '0532 111 44 22', '34 ABC 123', '18.08.2026', '22.08.2026',
        'Açık', '120,00', '480,00', '300,00', '180,00', '3.000,00', 'TL'],
      ['CR-2043', 'Leyla Hicazi', '0544 555 66 77', '34 XYZ 789', '16.08.2026', '22.08.2026',
        'Açık', '60,00', '360,00', '360,00', '0,00', '150,00', 'USD'],
    ],
  },
  Arac: {
    headers: ['Plaka', 'Marka', 'Model', 'Yıl', 'Grup', 'Durum', 'Şube', 'Km'],
    rows: [['34 ABC 123', 'Hyundai', 'Accent', '2023', 'Ekonomik', 'Kirada', 'Taksim', '48210']],
  },
  Musteri: {
    headers: ['Müşteri No', 'Ad Soyad', 'Telefon', 'TC Kimlik', 'Ehliyet'],
    rows: [
      ['C-501', 'Ahmet Nassar', '0532 111 44 22', '12345678901', 'DL-88231'],
      ['C-502', 'Leyla Hicazi', '0544 555 66 77', '98765432109', 'DL-77120'],
    ],
  },
  // الدفتر يشير إلى العقد لا إلى العميل — وهذا ما يجب أن يصل بينهما
  CariHesap: {
    headers: ['Tarih', 'Açıklama', 'Belge No', 'Borç', 'Alacak', 'Bakiye', 'Para Birimi'],
    rows: [
      ['18.08.2026', 'Depozito', 'CR-2041', '0,00', '3.000,00', '3.000,00', 'TL'],
      ['20.08.2026', 'Ek gün', 'CR-2041', '120,00', '0,00', '2.880,00', 'TL'],
    ],
  },
};

const MENU = `<nav>
<a href="/Sozlesme/Index">İşlemler</a><a href="/Arac/Index">Tanımlar</a>
<a href="/Musteri/Index">Kayıtlar</a><a href="/CariHesap/Index">Finans</a>
<a href="/Account/LogOff">Çıkış</a></nav>`;

const tableHtml = (t) => `<table><thead><tr>${t.headers.map((h) => `<th>${h}</th>`).join('')}</tr></thead>
<tbody>${t.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody></table>`;

function startPanel() {
  const pairs = new Map();
  const cookieOf = (req, name) =>
    (req.headers.cookie || '').split(';').map((s) => s.trim())
      .find((s) => s.startsWith(`${name}=`))?.slice(name.length + 1);

  const login = (res, err = '') => {
    const ck = crypto.randomBytes(8).toString('hex');
    const fd = crypto.randomBytes(8).toString('hex');
    pairs.set(ck, fd);
    res.writeHead(200, {
      'Content-Type': 'text/html; charset=utf-8',
      'Set-Cookie': `__RequestVerificationToken=${ck}; Path=/`,
    });
    res.end(`<!doctype html><title>Giriş - Eganis</title>
      ${err ? `<div class="validation-summary-errors">${err}</div>` : ''}
      <form method="post" action="/Account/Login">
      <input type="hidden" name="__RequestVerificationToken" value="${fd}">
      <input type="text" name="UserName"><input type="password" name="Password">
      <input type="checkbox" name="RememberMe" value="true">
      <input type="hidden" name="RememberMe" value="false">
      <button type="submit">Giriş Yap</button></form>`);
  };

  const server = http.createServer((req, res) => {
    const url = req.url.split('?')[0];

    if (url === '/Account/Login' && req.method === 'POST') {
      let raw = '';
      req.on('data', (c) => { raw += c; });
      req.on('end', () => {
        const body = new URLSearchParams(raw);
        if (pairs.get(cookieOf(req, '__RequestVerificationToken'))
            !== body.get('__RequestVerificationToken')) {
          return login(res, 'Doğrulama hatası.');
        }
        if (body.get('UserName') === USER && body.get('Password') === PASS) {
          res.writeHead(302, { 'Set-Cookie': 'sid=ok; Path=/', Location: '/' });
          return res.end();
        }
        return login(res, 'Giriş başarısız, lütfen geçerli kullanıcı adı ve şifrenizi giriniz.');
      });
      return;
    }

    if (cookieOf(req, 'sid') !== 'ok') {
      if (url !== '/Account/Login') {
        res.writeHead(302, { Location: '/Account/Login?ReturnUrl=%2F' });
        return res.end();
      }
      return login(res);
    }

    const key = url.split('/')[1];
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return res.end(TABLES[key]
      ? `<!doctype html><title>${key}</title>${MENU}${tableHtml(TABLES[key])}`
      : `<!doctype html><title>Eganis Panel</title>${MENU}<h1>Hoş geldiniz</h1>`);
  });

  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => resolve({ server, port: server.address().port }));
  });
}

async function driverFor(port, password = PASS) {
  process.env.EGANIS_BASE_URL = `http://127.0.0.1:${port}/Account/Login?ReturnUrl=%2F`;
  process.env.EGANIS_USERNAME = USER;
  process.env.EGANIS_PASSWORD = password;
  process.env.EGANIS_LOGIN_VIA_BROWSER = 'never'; // الاختبار بلا متصفّح
  process.env.EGANIS_CACHE_SECONDS = '0';
  const { config, panelBase } = await import('../src/config.js');
  config.eganis.baseUrl = panelBase(process.env.EGANIS_BASE_URL);
  config.eganis.username = USER;
  config.eganis.password = password;
  config.eganis.loginViaBrowser = 'never';
  config.eganis.cacheSeconds = 0;
  config.eganis.pages = '';
  const { createHttpDriver } = await import('../src/connectors/eganis/http.js');
  return createHttpDriver();
}

test('دخول ASP.NET كامل ثم اكتشاف الصفحات من محتواها', async (t) => {
  const { server, port } = await startPanel();
  t.after(() => server.close());

  const driver = await driverFor(port);
  const { found } = await driver.autodetect({});
  assert.deepEqual(
    Object.keys(found).sort(),
    ['contracts', 'customers', 'ledger', 'vehicles'],
  );
  assert.equal(found.contracts.href, '/Sozlesme/Index');
  assert.equal(found.ledger.href, '/CariHesap/Index');
});

test('الجداول التركية تتحوّل إلى سجلات كاملة', async (t) => {
  const { server, port } = await startPanel();
  t.after(() => server.close());

  const driver = await driverFor(port);
  const [contract] = await driver.listContracts();
  assert.equal(contract.no, 'CR-2041');
  assert.equal(contract.customerName, 'Ahmet Nassar');
  assert.equal(contract.plate, '34 ABC 123');
  assert.equal(contract.status, 'open');
  assert.equal(contract.deposit, 3000); // 3.000,00 التركية
  assert.equal(contract.balance, 180);
  assert.equal(contract.currency, 'TRY'); // TL
  assert.equal(contract.startAt, '2026-08-18T00:00:00'); // بلا انزياح يوم

  const [vehicle] = await driver.listVehicles();
  assert.equal(vehicle.status, 'rented'); // Kirada
  assert.equal(vehicle.odometer, 48210);
});

test('حركات الدفتر تُنسب لصاحبها عبر رقم عقده لا رقمه', async (t) => {
  const { server, port } = await startPanel();
  t.after(() => server.close());

  const driver = await driverFor(port);

  // دفتر eganis يحمل «Belge No» = رقم العقد، ولا يذكر رقم العميل إطلاقاً
  const his = await driver.listLedgerEntries('C-501');
  assert.equal(his.length, 2, 'يجب أن تصل حركتا عقده إليه');
  assert.equal(his[0].type, 'payment'); // Alacak
  assert.equal(his[1].type, 'extra'); // Borç
  assert.equal(his[0].amount, 3000);

  // ولا تتسرّب إلى عميل آخر لا عقد له في الدفتر
  assert.deepEqual(await driver.listLedgerEntries('C-502'), []);
});

test('العملة الثانية تُقرأ كما هي من اللوحة', async (t) => {
  const { server, port } = await startPanel();
  t.after(() => server.close());

  const driver = await driverFor(port);
  const usd = (await driver.listContracts()).find((c) => c.no === 'CR-2043');
  assert.equal(usd.currency, 'USD');
});

test('بيانات دخول خاطئة تُعيد رسالة اللوحة نفسها', async (t) => {
  const { server, port } = await startPanel();
  t.after(() => server.close());

  const driver = await driverFor(port, 'YanlisSifre');
  const result = await driver.loginDiagnose();
  assert.equal(result.ok, false);
  assert.match(result.error, /Giriş başarısız/);
  // ويصف النموذج كما هو فعلاً
  assert.match(result.summary, /UserName/);
  assert.match(result.summary, /__RequestVerificationToken/);
});
