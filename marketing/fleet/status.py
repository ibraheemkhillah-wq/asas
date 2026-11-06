"""Status / price card for fleet album images: a white rounded card in the sky.
One or more lines; a line may have an emoji on both sides, e.g.
    «✅ تم الحجز ✅»
    «هونداي بايون 2023» + «🔥 7 أيام / $250 🔥»
usage: python3 status.py <album.jpg> <out.jpg> "<line>[|emoji]" ["<line>[|emoji]" ...]"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'brand-kit'))
import brand as B

EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
INK = (17, 17, 17)

def emoji(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)                     # colour emoji only render at 109
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor='mm')
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)

def card(fr, lines, top=150, fsize=None, gap=42, padx=60, pady=44, lead=1.42):
    """lines: [(text, emoji_or_None), ...]; centred horizontally, top edge at `top`"""
    W = fr.width
    fsize = fsize or (100 if len(lines) == 1 else 84)
    font = B.F(B.AR_BLACK, fsize)
    d = ImageDraw.Draw(fr)
    rows = []
    for text, ch in lines:
        text = ltr_runs(text)
        tw = d.textlength(text, font=font, direction='rtl', language='ar')
        e = emoji(ch, int(fsize * 0.95)) if ch else None
        rows.append((text, e, tw + (2 * (e.width + gap) if e else 0)))
    lh = int(fsize * lead)
    pw = max(r[2] for r in rows) + 2 * padx
    ph = lh * len(rows) + 2 * pady - int(fsize * (lead - 1.0))
    x0 = (W - pw) // 2; y0 = top; rad = min(56, ph // 3)
    sh = Image.new('RGBA', fr.size, (0, 0, 0, 0))               # soft drop shadow lifts it off the sky
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 10, x0 + pw, y0 + ph + 10), radius=rad, fill=(10, 30, 60, 70))
    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=rad, fill=(255, 255, 255, 255))
    for i, (text, e, w) in enumerate(rows):
        cy = y0 + pady + fsize // 2 + i * lh
        pos = (W / 2, cy + fsize * 0.06)
        d.text(pos, text, font=font, fill=INK, anchor='mm', direction='rtl', language='ar')
        if e:                                   # emojis sit a fixed gap outside the real ink edges
            ink = Image.new('L', fr.size, 0)
            ImageDraw.Draw(ink).text(pos, text, font=font, fill=255, anchor='mm', direction='rtl', language='ar')
            l, _, r, _ = ink.getbbox()
            ey = cy - e.height // 2
            fr.alpha_composite(e, (int(l - gap - e.width), ey))
            fr.alpha_composite(e, (int(r + gap), ey))
    return fr

def ltr_runs(text):
    """keep prices like $250 in reading order inside Arabic text (wrap them in LTR isolates)"""
    import re
    return re.sub(r'([$€₺]?\d[\d.,]*[$€₺]?)', '\u2066\\1\u2069', text)

def badge(fr, text, ch='✅', **kw):
    return card(fr, [(text, ch)], **kw)

if __name__ == '__main__':
    src, out = sys.argv[1:3]
    lines = [(a.split('|')[0], a.split('|')[1] if '|' in a else None) for a in sys.argv[3:]]
    fr = Image.open(src).convert('RGBA')
    card(fr, lines).convert('RGB').save(out, quality=95)
    print(out)
