# CALL & RENT — نظام إدارة عمليات التشغيل
#
# يتضمّن Chromium والخطوط العربية لأنهما لازمان لأمرين:
#   1) توليد كشوف الحساب PDF بعربية صحيحة التشكيل
#   2) قراءة لوحة eganis في وضع المتصفّح
FROM node:22-bookworm-slim

ENV NODE_ENV=production \
    TZ=Europe/Istanbul \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 \
    PDF_CHROME_PATH=/usr/bin/chromium \
    PLAYWRIGHT_CHROMIUM_PATH=/usr/bin/chromium

RUN apt-get update && apt-get install -y --no-install-recommends \
      chromium \
      fonts-noto-core \
      fonts-noto-color-emoji \
      ca-certificates \
      tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# طبقة الاعتماديات منفصلة ليُعاد استخدامها بين النشرات
COPY package*.json ./
RUN npm install --omit=dev && npm cache clean --force

COPY . .

# قاعدة البيانات والملفات المرفوعة وجلسة eganis — تحتاج قرصاً دائماً
RUN mkdir -p data && chown -R node:node /app
VOLUME ["/app/data"]

USER node
EXPOSE 3000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s \
  CMD node -e "fetch('http://127.0.0.1:'+(process.env.PORT||3000)+'/api/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "src/server.js"]
