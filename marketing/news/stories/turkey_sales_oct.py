"""Turkey car + light-commercial sales, October 2026 (ODMD), light theme. Images: Canva AI."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "turkey-sales-oct"
THEME = "light"
SOURCE = "المصدر: جمعية موزعي السيارات في تركيا ODMD"
SLIDES = [
    dict(kind='cover', bg='tr-sales-1-cover.jpg', mark='flag-turkey.png', mark_w=200, stack=[
        ('مبيعات السيارات في تركيا', LOGONAVY, Wh, 60),
        ('تتراجع 30.8%', Wh, LOGONAVY, 84),
        ('في أكتوبر 2026', O, LOGONAVY, 70)]),
    dict(kind='inner', bg='tr-sales-2-cars.jpg', chip='الأرقام',
         title=[('80,334 مركبة', O), ('فقط في أكتوبر', Wh)],
         body=[('تراجعت مبيعات السيارات والمركبات التجارية الخفيفة في تركيا بنسبة', Wh), ('30.84%', O),
               ('مقارنةً بأكتوبر من العام الماضي، لتبلغ', Wh), ('80,334 مركبة،', O),
               ('وهو أدنى مستوى لهذا الشهر منذ عام 2023.', Wh)]),
    dict(kind='inner', bg='tr-sales-3-vans.jpg', chip='حسب الفئة',
         title=[('التجارية الخفيفة', Wh), ('الأكثر تراجعاً', O)],
         body=[('انخفضت مبيعات السيارات الخاصة بنسبة', Wh), ('28.4%', O), ('إلى', Wh), ('64,939 سيارة،', O),
               ('بينما تراجعت المركبات التجارية الخفيفة بنسبة', Wh), ('39.5%', O), ('إلى', Wh), ('15,395 مركبة.', O),
               ('\n', Wh), ('ومنذ بداية العام، تراجع السوق بنسبة', Wh), ('15.3%.', O)]),
    dict(kind='ask', bg='tr-sales-4-ask.jpg', chip='شاركنا رأيك', top=380, lines=[
        ('برأيك.. هل غلاء الأسعار', LOGONAVY, 66),
        ('هو ما أبعد الناس', LOGONAVY, 66),
        ('عن شراء السيارات؟', O, 84)]),
]
