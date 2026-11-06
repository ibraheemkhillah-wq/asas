"""Status badge for fleet album images: a white pill in the sky, e.g. «✅ تم الحجز ✅».
usage: python3 status.py <album.jpg> <out.jpg> "<text>" [emoji]"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'brand-kit'))
import brand as B

EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

def emoji(ch, size):
    from PIL import ImageFont
    f = ImageFont.truetype(EMOJI_FONT, 109)                     # colour emoji only render at 109
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor='mm')
    im = im.crop(im.getbbox())
    return im.resize((size, int(size * im.height / im.width)), Image.LANCZOS)

def badge(fr, text, ch='✅', cy=300, fsize=104, esize=104, color=(17, 17, 17)):
    W = fr.width
    font = B.F(B.AR_BLACK, fsize)
    d = ImageDraw.Draw(fr)
    tb = d.textbbox((0, 0), text, font=font, anchor='lm', direction='rtl', language='ar')
    tw = tb[2] - tb[0]
    e = emoji(ch, esize); gap = 34; padx = 56
    pw = tw + 2 * (e.width + gap) + 2 * padx; ph = int(max(esize, fsize) * 1.75)
    x0 = (W - pw) // 2; y0 = cy - ph // 2
    # soft drop shadow so the pill lifts off the sky
    sh = Image.new('RGBA', fr.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + 10, x0 + pw, y0 + ph + 10), radius=ph // 2.6, fill=(10, 30, 60, 70))
    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=ph // 2.6, fill=(255, 255, 255, 255))
    ey = cy - e.height // 2
    fr.alpha_composite(e, (x0 + padx, ey))
    fr.alpha_composite(e, (x0 + pw - padx - e.width, ey))
    d.text((W / 2, cy + fsize * 0.06), text, font=font, fill=color, anchor='mm', direction='rtl', language='ar')
    return fr

if __name__ == '__main__':
    src, out, text = sys.argv[1:4]; ch = sys.argv[4] if len(sys.argv) > 4 else '✅'
    fr = Image.open(src).convert('RGBA')
    badge(fr, text, ch).convert('RGB').save(out, quality=95)
    print(out)
