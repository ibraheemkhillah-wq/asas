"""Turkey traffic fines 2027 (projected, 27.83% revaluation), dark theme. Images: Canva AI."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "turkey-fines-2027"
THEME = "dark"
SOURCE = "المصدر: هابرتورك و CNBC-e"
NOTE = 'مبالغ متوقعة تُعتمد رسمياً في ديسمبر 2026'
SLIDES = [
    dict(kind='cover', bg='fines-1-cover.jpg', stack=[
        ('مخالفات السير في تركيا', LOGONAVY, Wh, 60),
        ('غرامات جديدة لعام 2027', Wh, LOGONAVY, 76),
        ('بزيادة 27.83%', O, LOGONAVY, 72)]),
    dict(kind='stats', bg='fines-1-cover.jpg', chip='المخالفات الأعلى غرامة',
         total='27.83%', total_label='نسبة الزيادة من 1 يناير 2027', note=NOTE, rh=116, rows=[
            ('التفحيط (الدرفت)', '178,962 TL', 178962),
            ('تغيير المسارات بتهوّر', '115,047 TL', 115047),
            ('القيادة بلا لوحة', '58,801 TL', 58801),
            ('القيادة تحت تأثير الكحول', '31,957 TL', 31957)]),
    dict(kind='stats', bg='fines-1-cover.jpg', chip='مخالفات يومية شائعة',
         total='38,349 TL', total_label='أعلى غرامة لتجاوز السرعة', note=NOTE, rh=116, rows=[
            ('تجاوز الإشارة الحمراء', '6,391 TL', 6391),
            ('استخدام الهاتف أثناء القيادة', '6,391 TL', 6391),
            ('عدم ربط حزام الأمان', '3,195 TL', 3195),
            ('عدم ارتداء خوذة الدراجة', '3,195 TL', 3195)]),
    dict(kind='ask', bg='fines-1-cover.jpg', chip='شاركنا رأيك', top=380, lines=[
        ('برأيك.. هل تكفي الغرامات', Wh, 64),
        ('المرتفعة لتقليل المخالفات', Wh, 64),
        ('في الطرق؟', O, 92)]),
]
