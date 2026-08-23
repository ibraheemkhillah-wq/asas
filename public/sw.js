/* عامل خدمة: يجعل التطبيق يفتح فوراً على الموبايل ويعمل بلا شبكة عند الحاجة.
 *
 * الشبكة أولاً للواجهة: النسخة المحفوظة كانت تُقدَّم على الجديدة، فيبقى المستخدم
 * يرى واجهة قديمة بعد كل تحديث. الآن نجلب الأحدث ونرجع للمحفوظ فقط عند انقطاع
 * الشبكة. وطلبات البيانات (api/) لا تُخزَّن أصلاً.
 */
const CACHE = 'callrent-shell-v2';
const SHELL = ['/', '/index.html', '/styles.css', '/app.js', '/manifest.webmanifest'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) => cache.addAll(SHELL))
      .catch(() => {}) // تعذّر التخزين لا يمنع التثبيت
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin) return;

  // البيانات والصور المولّدة: من الشبكة دائماً
  if (url.pathname.startsWith('/api/')) return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        }
        return response;
      })
      .catch(() => caches.match(event.request).then((cached) => cached || caches.match('/'))),
  );
});
