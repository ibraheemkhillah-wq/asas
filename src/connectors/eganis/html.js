/**
 * قراءة HTML بلا متصفّح.
 *
 * لماذا؟ لأن تشغيل Chromium لقراءة جدول يستهلك مئات الميجابايتات، وخطة
 * الاستضافة الصغيرة (٥١٢ ميجا) تسقط تحته فيتوقّف التطبيق كلّه. وصفحات لوحة
 * eganis صفحات ASP.NET عادية: الجداول موجودة في نصّ الصفحة نفسه، فقراءتها
 * نصّاً تكفي وتستهلك عشرات الميجابايتات لا مئاتها.
 *
 * ليس محلّل HTML كامل المواصفات، بل قدرٌ يكفي للوحات الإدارة: جداول
 * ونماذج وروابط. وما لا يفهمه يتجاهله بدل أن يتعطّل.
 */

const ENTITIES = {
  amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', shy: '',
  aacute: 'á', ccedil: 'ç', uuml: 'ü', ouml: 'ö', ccedilupper: 'Ç',
};

/** فكّ رموز HTML — العددية منها والمسمّاة */
export function decodeEntities(text) {
  return String(text ?? '')
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => safeChar(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => safeChar(parseInt(dec, 10)))
    .replace(/&([a-z]+[0-9]*);/gi, (whole, name) => {
      const key = name.toLowerCase();
      return ENTITIES[key] !== undefined ? ENTITIES[key] : whole;
    });
}

function safeChar(code) {
  try {
    return String.fromCodePoint(code);
  } catch {
    return '';
  }
}

/** نصّ خالص من شذرة HTML: بلا وسوم ولا سكربتات ولا فراغات زائدة */
export function textOf(html) {
  return decodeEntities(
    String(html ?? '')
      .replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, ' ')
      .replace(/<br\s*\/?>/gi, ' ')
      .replace(/<[^>]*>/g, ' '),
  )
    .replace(/\s+/g, ' ')
    .trim();
}

const ATTR_RE = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

/** سمات وسم واحد كـ {name: value} */
export function attrsOf(tagHtml) {
  const out = {};
  // نتجاوز اسم الوسم نفسه ثم نقرأ ما بعده
  const body = String(tagHtml ?? '').replace(/^<\s*[a-zA-Z0-9-]+/, '');
  for (const m of body.matchAll(ATTR_RE)) {
    const value = m[3] ?? m[4] ?? m[5] ?? '';
    out[m[1].toLowerCase()] = decodeEntities(value);
  }
  return out;
}

/**
 * مواضع كل عنصر من نوع معيّن مع محتواه، بوعي بالتداخل.
 * الجداول داخل الجداول شائعة في اللوحات القديمة، فالمطابقة الكسولة تقطع
 * الجدول الخارجي عند أول `</table>` تصادفه وتُفسد كل ما بعده.
 */
/*
 * وسوم يُغلقها ضمنياً ظهورُ وسم مثلها. الصفوف والخلايا كثيراً ما تُكتب بلا
 * وسم إغلاق (`<td>a<td>b`) وهو HTML صحيح، فلولا هذا لابتلع الصفّ الأول
 * بقيّة الجدول.
 */
const IMPLICIT_CLOSE = new Set(['tr', 'td', 'th', 'li', 'option', 'p']);

export function findElements(html, tagName) {
  const source = String(html ?? '');
  const tag = tagName.toLowerCase();
  const implicit = IMPLICIT_CLOSE.has(tag);
  const scanner = new RegExp(`<${tag}\\b[^>]*>|</${tag}\\s*>`, 'gi');
  const found = [];
  const stack = [];

  const close = (open, endIndex) => {
    found.push({
      at: open.start,
      openTag: open.tag,
      attrs: attrsOf(open.tag),
      inner: source.slice(open.end, endIndex),
    });
  };

  for (const match of source.matchAll(scanner)) {
    if (match[0].startsWith('</')) {
      const open = stack.pop();
      if (open) close(open, match.index);
      continue;
    }
    // وسم مغلق ذاتياً لا يفتح محتوى
    if (match[0].endsWith('/>')) continue;
    // وسم مثله مفتوح أمامنا ولا يقبل التداخل = إغلاق ضمني
    if (implicit && stack.length) close(stack.pop(), match.index);
    stack.push({ tag: match[0], start: match.index, end: match.index + match[0].length });
  }

  // وسوم فُتحت ولم تُغلق (HTML غير مكتمل) — نأخذ ما بقي من الصفحة
  for (const open of stack) close(open, source.length);

  // بترتيب ظهورها في الصفحة، لأن التداخل يجعل الداخلي يُغلق قبل الحاوي
  return found.sort((a, b) => a.at - b.at);
}

/** خلايا صفّ واحد بترتيبها في الصفّ، سواء كانت td أو th */
function cellsOf(rowHtml) {
  const source = String(rowHtml ?? '');
  const scanner = /<(t[dh])\b[^>]*>|<\/(t[dh])\s*>/gi;
  const cells = [];
  let openAt = -1;
  let depth = 0;

  for (const match of source.matchAll(scanner)) {
    if (match[1]) {
      if (depth === 0) openAt = match.index + match[0].length;
      depth += 1;
    } else if (depth > 0) {
      depth -= 1;
      if (depth === 0) cells.push(textOf(source.slice(openAt, match.index)));
    }
  }

  if (cells.length) return cells;

  // صفّ بخلايا بلا وسوم إغلاق — نقسم على بدايات الخلايا
  return source
    .split(/<t[dh]\b[^>]*>/i)
    .slice(1)
    .map((part) => textOf(part));
}

/**
 * كل جداول الصفحة: ترويسة وصفوف نصّية — نفس الشكل الذي يعطيه المتصفّح،
 * ليعمل عليها `auto-map.js` بلا تغيير.
 */
export function extractTables(html) {
  return findElements(html, 'table').map((table) => {
    // نُسقط الجداول المتداخلة حتى لا تختلط صفوفها بصفوف الجدول الحاوي
    const own = table.inner.replace(/<table\b[\s\S]*?<\/table\s*>/gi, ' ');

    const heads = findElements(own, 'thead');
    let headers = heads.length
      ? findElements(heads[0].inner, 'th').map((th) => textOf(th.inner))
      : [];

    const bodies = findElements(own, 'tbody');
    const rowSource = bodies.length ? bodies.map((b) => b.inner).join('') : own;
    let rows = findElements(rowSource, 'tr').map((tr) => cellsOf(tr.inner));

    // بلا thead: الصفّ الأول هو الترويسة
    if (!headers.length && rows.length) {
      const first = findElements(own, 'tr')[0];
      if (first) {
        headers = cellsOf(first.inner);
        if (!bodies.length) rows = rows.slice(1);
      }
    }

    return { headers, rows: rows.filter((cells) => cells.some((c) => c)) };
  });
}

/** روابط الصفحة كما يراها المتصفّح: نصّ الرابط وعنوانه */
export function extractLinks(html) {
  return findElements(html, 'a')
    .map((a) => ({ text: textOf(a.inner).slice(0, 60), href: a.attrs.href || '' }))
    .filter((l) => l.href && !/^(javascript:|#|mailto:|tel:)/i.test(l.href));
}

/** حقول نموذج واحد بأسمائها وقيمها الحالية */
function fieldsOf(formHtml) {
  const fields = [];

  for (const m of formHtml.matchAll(/<input\b[^>]*>/gi)) {
    const a = attrsOf(m[0]);
    fields.push({
      tag: 'input',
      type: (a.type || 'text').toLowerCase(),
      name: a.name || '',
      id: a.id || '',
      value: a.value || '',
      placeholder: a.placeholder || '',
      required: 'required' in a,
      checked: 'checked' in a,
    });
  }

  for (const select of findElements(formHtml, 'select')) {
    const options = findElements(select.inner, 'option');
    const chosen = options.find((o) => 'selected' in o.attrs) || options[0];
    fields.push({
      tag: 'select',
      type: 'select',
      name: select.attrs.name || '',
      id: select.attrs.id || '',
      value: chosen ? (chosen.attrs.value ?? textOf(chosen.inner)) : '',
      placeholder: '',
      required: 'required' in select.attrs,
    });
  }

  for (const area of findElements(formHtml, 'textarea')) {
    fields.push({
      tag: 'textarea',
      type: 'textarea',
      name: area.attrs.name || '',
      id: area.attrs.id || '',
      value: textOf(area.inner),
      placeholder: area.attrs.placeholder || '',
      required: 'required' in area.attrs,
    });
  }

  return fields;
}

/** نماذج الصفحة، ولكل نموذج وجهته وحقوله وأزراره */
export function extractForms(html) {
  return findElements(html, 'form').map((form) => ({
    action: form.attrs.action || '',
    method: (form.attrs.method || 'GET').toUpperCase(),
    fields: fieldsOf(form.inner),
    buttons: [...form.inner.matchAll(/<button\b[^>]*>|<input\b[^>]*type=["']?submit["']?[^>]*>/gi)]
      .map((m) => attrsOf(m[0]))
      .map((a) => ({ type: (a.type || '').toLowerCase(), text: a.value || '' })),
    labels: findElements(form.inner, 'label').map((l) => ({
      forId: l.attrs.for || '',
      text: textOf(l.inner).slice(0, 40),
    })),
  }));
}

/** النموذج الذي يحوي حقل كلمة سر — نموذج الدخول */
export function findLoginForm(html) {
  return extractForms(html).find((f) => f.fields.some((x) => x.type === 'password')) || null;
}

/** هل الصفحة صفحة دخول؟ وجود حقل كلمة سر هو الدليل العملي */
export function looksLikeLogin(html) {
  return /<input\b[^>]*type=["']?password["']?/i.test(String(html ?? ''));
}

/**
 * رسائل الرفض التي تكتبها اللوحة — من الحاويات المعروفة، وإن لم توجد فمن
 * أي نصّ ظاهر يحمل كلمة رفض تركية.
 */
const ERROR_CLASS =
  /class=["'][^"']*(validation-summary-errors|field-validation-error|alert-danger|alert-error|text-danger|error-message|invalid-feedback|toast-error)[^"']*["']/i;
const REJECT_WORDS =
  /(hatal|yanlış|yanlis|geçersiz|gecersiz|zorunlu|boş bırak|bos birak|kilitli|başarısız|basarisiz|bulunamadı|bulunamadi)/i;

export function extractErrors(html) {
  const source = String(html ?? '');
  const messages = [];

  for (const tag of ['div', 'span', 'p', 'li', 'ul']) {
    for (const el of findElements(source, tag)) {
      if (!ERROR_CLASS.test(el.openTag)) continue;
      const text = textOf(el.inner);
      if (text) messages.push(text);
    }
  }

  if (!messages.length) {
    for (const tag of ['div', 'span', 'p', 'li']) {
      for (const el of findElements(source, tag)) {
        const text = textOf(el.inner);
        if (text && text.length < 160 && REJECT_WORDS.test(text)) messages.push(text);
      }
    }
  }

  return [...new Set(messages)].slice(0, 4);
}
