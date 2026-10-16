"""Tesla Roadster (2nd gen) reveal, 15 Oct 2026 (global news, dark theme).
Photos: Tesla, Inc. (official stills and livestream frames), credited on every slide."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "tesla-roadster"
THEME = "dark"
SOURCE = "المصدر: TechCrunch و Fox Business"
PHOTO = 'Photo: Tesla'
SLIDES = [
    dict(kind='cover', bg='roadster-1-cover.jpg', credit=PHOTO, stack=[
        ('تسلا تكشف رودستر الجديدة', LOGONAVY, Wh, 60),
        ('سيارة تقفز وتطير!', Wh, LOGONAVY, 84),
        ('الإنتاج في 2028', O, LOGONAVY, 72)]),
    dict(kind='inner', bg='roadster-2-demo.jpg', chip='العرض', credit=PHOTO,
         title=[('تقفز وتدور', O), ('في الهواء', Wh)],
         body=[('صعدت السيارة منحدراً مقلوباً بنظام شفط، ثم أطلقت', Wh), ('دفعات من الهواء المضغوط', O),
               ('عبر محركات دفع مدمجة لتقفز وتدور في الهواء وتهبط من جديد، كما', Wh), ('قفزت فوق صف من سيارات تسلا', O),
               ('أثناء سيرها.', Wh)]),
    dict(kind='inner', bg='roadster-3-performance.jpg', chip='الأداء', credit=PHOTO,
         title=[('أقل من ثانية', O), ('إلى 96 كم/س', Wh)],
         body=[('بحسب تسلا، تصل فئة Thrust', Wh), ('من الثبات إلى 96 كم/س في أقل من ثانية،', O),
               ('وتتجاوز السرعة القصوى للسيارة', Wh), ('370 كم/س،', O), ('ويبلغ مداها', Wh), ('نحو 480 كيلومتراً.', O)]),
    dict(kind='inner', bg='roadster-4-trims.jpg', chip='الفئات', credit=PHOTO,
         title=[('ثلاث فئات', Wh), ('لرودستر الجديدة', O)],
         body=[('Performance', O), (': مقعدان، والحجز 50,000 دولار', Wh), ('\n', Wh),
               ('Thrust', O), (': محركات دفع، والحجز 250,000 دولار', Wh), ('\n', Wh),
               ('Rocket', O), (': مقعد واحد وطيران كامل، بدعوة خاصة', Wh)]),
    dict(kind='inner', bg='roadster-5-production.jpg', chip='الإنتاج', credit=PHOTO,
         title=[('الإنتاج يبدأ', Wh), ('عام 2028', O)],
         body=[('لم تعلن تسلا عن', Wh), ('السعر النهائي', O), ('للسيارة، فيما أكد مسؤولو الشركة أن', Wh),
               ('الإنتاج سيبدأ عام 2028،', O), ('بعد تأجيلات متكررة منذ الكشف الأول عنها عام 2017.', Wh)]),
    dict(kind='ask', bg='roadster-6-ask.jpg', chip='شاركنا رأيك', top=760, credit=PHOTO, lines=[
        ('لو أضفنا رودستر الطائرة', Wh, 58),
        ('إلى أسطول CALL & RENT…', Wh, 58),
        ('أين نسلّمك إياها؟', O, 96)]),
]
