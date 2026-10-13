"""Stamp the fixed 'وفّر معنا' offers badge on the winter-offer poster.

usage: python3 winter_offer_badge.py <brand-kit dir> <src.jpg> <out.png>
"""
import sys
sys.path.insert(0, sys.argv[1])
from PIL import Image, ImageDraw
from brand import F, AR_BOLD, LOGONAVY, WHITE, w_ar

OFFER_RED = (200, 30, 45)          # #C81E2D, same plate as the news template's 'offer' section
LABEL = 'وفّر معنا'
cv = Image.open(sys.argv[2]).convert('RGBA'); d = ImageDraw.Draw(cv)
W = cv.width; R_ = W - 64
fb = F(AR_BOLD, 26); bh = 58; by = 50
bw = w_ar(LABEL, fb) + 64; bx = R_ - bw
d.rounded_rectangle((bx, by, bx+bw, by+bh), radius=6, fill=OFFER_RED+(255,))
d.polygon([(bx, by+bh-22), (bx, by+bh), (bx+22, by+bh)], fill=LOGONAVY+(255,))
d.text((bx+bw/2, by+bh/2+2), LABEL, font=fb, fill=WHITE+(255,), anchor='mm', direction='rtl', language='ar')
cv.convert('RGB').save(sys.argv[3]); print(sys.argv[3])
