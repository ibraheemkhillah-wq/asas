# تركيب التطبيق على خادم (VPS)

الهدف: التطبيق يعمل ٢٤ ساعة، تفتحه من جوالك ومن المكتب، ويستقبل ويبهوك واتساب.

المواصفات الكافية: **1 vCPU · 2 GB RAM · 20 GB قرص** — أي خطة اقتصادية عند
Hetzner أو DigitalOcean أو Contabo تكفي. اختر مركز بيانات قريباً (ألمانيا أو تركيا)
ليكون الاتصال أسرع من إسطنبول.

---

## ١) تجهيز الخادم

```bash
# على أوبونتو 24.04
sudo apt update && sudo apt upgrade -y

# Node.js 22 (التطبيق يحتاج 22.5 أو أحدث)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs git

# المتصفّح والخطوط العربية — لتوليد كشوف PDF
sudo apt install -y chromium-browser fonts-noto-core fonts-noto-color-emoji
```

تأكّد: `node -v` يعطي `v22.x` أو أعلى.

## ٢) إنزال التطبيق وضبطه

```bash
sudo adduser --disabled-password --gecos "" callrent
sudo su - callrent

git clone https://github.com/ibraheemkhillah-wq/asas.git app
cd app
npm install --omit=dev
cp .env.example .env
nano .env
```

**الحد الأدنى في `.env`:**

```env
APP_TOKEN=<كلمة سر طويلة عشوائية — هذه حماية التطبيق كله>
PORT=3000
TZ=Europe/Istanbul

FX_SOURCE=harem
FX_USD_TRY=48            # سعر احتياطي عند انقطاع الشبكة

# eganis — املأها بعد خطوة الربط
EGANIS_DRIVER=mock
EGANIS_BASE_URL=

# واتساب — املأها بعد تفعيل Cloud API
WHATSAPP_DRIVER=mock

ANTHROPIC_API_KEY=       # للمحادثة معي داخل التطبيق
```

ولّد كلمة سر قوية: `openssl rand -base64 24`

```bash
npm run seed     # بيانات أولية
npm start        # جرّب سريعاً ثم أوقفه بـ Ctrl+C
```

## ٣) تشغيله كخدمة دائمة

```bash
exit    # ارجع لمستخدم الإدارة
sudo nano /etc/systemd/system/callrent.service
```

```ini
[Unit]
Description=CALL & RENT Ops
After=network.target

[Service]
Type=simple
User=callrent
WorkingDirectory=/home/callrent/app
ExecStart=/usr/bin/node src/server.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now callrent
sudo systemctl status callrent      # للتأكد
sudo journalctl -u callrent -f      # لمتابعة السجل
```

## ٤) نطاق و HTTPS

واتساب Cloud API **يرفض** الويبهوك بدون HTTPS، فهذه خطوة إلزامية إن أردت ربط واتساب.

وجّه نطاقاً (مثلاً `ops.callandrent.com`) إلى عنوان الخادم، ثم:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
sudo nano /etc/nginx/sites-available/callrent
```

```nginx
server {
    server_name ops.callandrent.com;
    client_max_body_size 30M;          # لرفع الملفات في المحادثة

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/callrent /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d ops.callandrent.com    # شهادة مجانية تتجدّد تلقائياً
```

## ٥) الجدار الناري

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

المنفذ 3000 يبقى مغلقاً من الخارج — كل شيء يمرّ عبر nginx بـ HTTPS.

## ٦) التحقق النهائي

```bash
curl -s "https://ops.callandrent.com/api/fx/check?token=$APP_TOKEN"     # مصادر سعر الصرف
curl -s "https://ops.callandrent.com/api/system/health?token=$APP_TOKEN" # حالة الموصلات
npm run eganis:check                                                     # الربط مع eganis
```

ثم افتح `https://ops.callandrent.com` من جوالك، أدخل `APP_TOKEN`، وأضِف التطبيق
للشاشة الرئيسية (Safari: مشاركة ← إضافة إلى الشاشة الرئيسية).

## ٧) النسخ الاحتياطي

كل ما يخصّك محلياً في مجلد `data/`: المحادثات، الردود المدرَّبة، الحركات اليدوية،
الملفات، أسعار الصرف. (بيانات eganis تبقى في eganis.)

```bash
# نسخة يومية 3 صباحاً، مع الاحتفاظ بآخر ١٤ يوماً
sudo crontab -u callrent -e
```

```cron
0 3 * * * cd /home/callrent/app && tar czf ~/backup-$(date +\%F).tgz data/ && find ~ -name 'backup-*.tgz' -mtime +14 -delete
```

## ٨) التحديث لاحقاً

```bash
sudo su - callrent
cd app && git pull && npm install --omit=dev
exit
sudo systemctl restart callrent
```

---

## ملاحظات أمنية

- `APP_TOKEN` هو الحارس الوحيد للتطبيق — اجعله طويلاً عشوائياً ولا تشاركه في مجموعات.
- `data/eganis-session.json` (إن استخدمت وضع المتصفّح) يعادل كلمة سر eganis — احمِه:
  `chmod 600 data/eganis-session.json`
- لا ترفع ملف `.env` ولا مجلد `data/` إلى git (مستثناة أصلاً).
- فعّل `ALLOW_WRITES=false` مؤقتاً إن أردت تشغيل النظام بوضع القراءة فقط أثناء التجربة.
