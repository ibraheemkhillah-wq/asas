"""Honda in-road wireless charging (global news, light theme). Images: Canva AI."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "honda-wireless"
THEME = "light"
SLIDES = [
    dict(kind='cover', bg='honda-1-cover.jpg', stack=[
        ('هوندا تطوّر شحناً لاسلكياً', LOGONAVY, Wh, 60),
        ('السيارة تشحن وهي تسير', Wh, LOGONAVY, 80),
        ('بدون توقف عند المحطة', O, LOGONAVY, 68)]),
    dict(kind='inner', bg='honda-2-tech.jpg', chip='التقنية',
         title=[('شحن لاسلكي', O), ('من داخل الطريق', Wh)],
         body=[('طوّرت هوندا تقنية تشحن المركبات الكهربائية', Wh), ('لاسلكياً أثناء سيرها،', O),
               ('بما فيها الشاحنات الكبيرة، عبر', Wh), ('وحدات شحن مدمجة داخل الطريق', O),
               ('تنقل الكهرباء إلى المركبة وهي تتحرك.', Wh)]),
    dict(kind='inner', bg='honda-3-japan.jpg', chip='الاختبار',
         title=[('اختبار على طريق سريع', Wh), ('في اليابان', O)],
         body=[('تخطط هوندا لاختبار التقنية مع شركتي «تايسي» و«تايسي روتيك» بدءاً من السنة المالية التي تبدأ في', Wh),
               ('أبريل 2027', O), ('أو بعدها، بهدف', Wh), ('تقليل الحاجة إلى التوقف للشحن.', O)]),
    dict(kind='inner', bg='honda-4-cost.jpg', chip='التكلفة', source='المصدر: رويترز',
         title=[('الجدوى الاقتصادية', Wh), ('لم تُحسم بعد', O)],
         body=[('بحسب رويترز، قالت هوندا إن', Wh), ('تكلفة النظام', O),
               ('مقارنةً بشبكات الشحن السريع التقليدية', Wh), ('ما زالت تحتاج إلى تقييم.', O)]),
    dict(kind='poll', bg='honda-5-poll.jpg', chip='شاركنا رأيك', q1='لو صارت الطرقات تشحن سيارتك...', q2='شو بتفضّل؟',
         options=[('وأنا ماشي', 'bolt', O, 800), ('بالمحطة', 'plug', Wh, 290)], tag_y=640, tag_dir='down',
         cta='جاوبنا بالتعليقات'),
]
