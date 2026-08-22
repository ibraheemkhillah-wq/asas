# طلب الوصول البرمجي من eganis

انسخ الرسالة التركية أدناه وأرسلها لمزوّد البرنامج (بريد الدعم أو مسؤول حسابك).
هي مكتوبة لتصل إلى الشخص التقني مباشرة وتطلب بالضبط ما يحتاجه الربط — لا أكثر.

> **قبل الإرسال:** ضع اسم شركتك ورقم حسابك في السطر الأول، ورقم هاتفك في آخرها.

---

## الرسالة (تركي — للإرسال كما هي)

```
Konu: Web Servis (API) erişim talebi — [ŞİRKET ADI] / Müşteri No: [HESAP NO]

Merhaba,

[ŞİRKET ADI] olarak Eganis Rent A Car programını kullanıyoruz. Kendi
verilerimizi okuyabilmek için kullandığımız iç yönetim uygulamamızı Eganis ile
entegre etmek istiyoruz.

Bunun için Web Servis (API) erişimi ve dokümantasyonu talep ediyoruz.
İhtiyacımız olan işlemler:

  1. Sözleşme listesi ve detayı (kiralama sözleşmeleri, tarih ve durum filtresiyle)
  2. Araç listesi ve araç durumları (müsait / kirada / bakımda)
  3. Rezervasyon listesi
  4. Müşteri arama ve müşteri bilgileri
  5. Müşteri cari hesap hareketleri (depozito, tahsilat, borç/alacak)
  6. Sözleşmeye/araca bağlı belgeler ve fotoğraflar (sözleşme PDF, sigorta poliçesi, araç fotoğrafları)

Ayrıca şunları öğrenmek istiyoruz:

  - API türü nedir? (REST/JSON, SOAP/XML)
  - Kimlik doğrulama nasıl yapılıyor? (API key, kullanıcı adı/şifre, token)
  - Test ortamı (sandbox) var mı?
  - Sözleşme ve cari hesap kayıtlarında para birimi (TL / USD) alanı dönüyor mu?
    Firmamız hem TL hem USD ile çalışıyor, bu alan bizim için önemli.
  - Salt-okunur (read-only) bir API kullanıcısı tanımlanabilir mi?

Dokümantasyonu ve erişim bilgilerini paylaşabilirseniz çok memnun oluruz.
Varsa ek ücret/koşul bilgisini de iletmenizi rica ederiz.

Teşekkürler,
[AD SOYAD] — [ŞİRKET ADI]
[TELEFON] · [E-POSTA]
```

---

## ترجمة سريعة لما طلبناه

- **وصول Web Service (API) لبيانات حسابك أنت** — لا ربط بروكر (البروكر شيء آخر: بيبيع حجوزات).
- ست عمليات: العقود · المركبات · الحجوزات · العملاء · حركات الحساب (الذمم) · المستندات والصور.
- أربعة أسئلة تقنية تحدّد لي كيف أكتب الربط: نوع الـ API، طريقة التوثيق، وجود بيئة تجريبية، **وهل يرجع حقل العملة (TL/USD)** — هذا مهم لمحاسبتك بالعملتين.
- **مستخدم API للقراءة فقط** — أفضل أمنياً: يقرأ ولا يعدّل شيئاً في نظامك.

## لما يردّوا

أرسل لي الرد كما هو (أو ملف التوثيق)، وأنا أعبّئ `config/eganis.json` وأشغّل الفحص:

```bash
npm run eganis:check
```

المطلوب منك بعدها: تشغيل الأمر وإرسال مخرجاته — وأزبّط كل سطر أحمر فيه.

## إذا رفضوا أو تأخّروا

لا ننتظرهم: نشتغل بأتمتة المتصفّح على نفس حسابك (`EGANIS_DRIVER=browser`) —
راجع قسم «الربط عبر المتصفّح» في README. النتيجة واحدة بالنسبة لك، والفرق أن الـ API
أسرع وأثبت، وأتمتة المتصفّح تتأثر إن غيّروا شكل الصفحات.
