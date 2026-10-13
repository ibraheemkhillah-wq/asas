"""Toyota RAV4 Plug-in Hybrid 2026 recall (global news, dark theme). Car photos: Wikimedia Commons CC0; warning, service and question shots: Canva AI."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "toyota-rav4-recall"
THEME = "dark"
SOURCE = "المصدر: Toyota Motor Corporation"
SLIDES = [
    dict(kind='cover', bg='rav4-1-cover.jpg', mark='toyota-wordmark-white.png', mark_w=230, stack=[
        ('تويوتا تعلن حملة استدعاء', LOGONAVY, Wh, 60),
        ('راف 4 الهجينة القابلة للشحن', Wh, LOGONAVY, 80),
        ('موديل 2026', O, LOGONAVY, 72)]),
    dict(kind='inner', bg='rav4-2-system.jpg', chip='الخلل',
         title=[('خطأ برمجي في وحدة', Wh), ('MG-ECU', O)],
         body=[('يكمن الخلل في', Wh), ('خطأ برمجي', O), ('داخل وحدة التحكم الإلكترونية لمولد المحرك', Wh), ('MG-ECU', O),
               ('وقد يؤدي في حالات معينة إلى', Wh), ('عدم عمل نظام التحكم في طاقة المحرك', O), ('بالشكل الصحيح.', Wh)]),
    dict(kind='inner', bg='rav4-3-warning.jpg', chip='الخطر',
         title=[('توقف مفاجئ', O), ('لنظام الدفع الهجين', Wh)],
         body=[('قد يتوقف نظام الدفع الهجين عن العمل بشكل مفاجئ أثناء القيادة، وخاصة عند', Wh), ('السرعات العالية.', O),
               ('عندها تضيء', Wh), ('أضواء التحذير', O), ('وقد تدخل السيارة في', Wh), ('وضع الحماية', O),
               ('أو تفقد قوة الدفع تماماً.', Wh)]),
    dict(kind='inner', bg='rav4-4-service.jpg', chip='الحل',
         title=[('تحديث برمجي', Wh), ('مجاني بالكامل', O)],
         body=[('ستُحدّث وكالات تويوتا ومراكز الصيانة المعتمدة برمجيات وحدة التحكم الإلكترونية', Wh), ('مجاناً بالكامل،', O),
               ('وسترسل الشركة', Wh), ('إشعارات رسمية', O), ('لمالكي السيارات المشمولة لمراجعة أقرب مركز صيانة.', Wh)]),
    dict(kind='stats', bg='rav4-5-scope.jpg', chip='النطاق عالمياً',
         total='50,078', total_label='سيارة مشمولة بالاستدعاء حول العالم',
         rows=[('الولايات المتحدة', '31,000', 31000), ('كندا', '7,846', 7846),
               ('أستراليا', '5,925', 5925), ('اليابان', '5,307', 5307)],
         note='يقتصر الاستدعاء على فئة الهجين القابل للشحن موديل 2026 فقط'),
    dict(kind='ask', bg='rav4-6-ask.jpg', chip='شاركنا رأيك', top=720, lines=[
        ('لو ظهرت أضواء التحذير فجأة', Wh, 64),
        ('في سيارتك المستأجرة..', Wh, 64),
        ('ماذا تفعل أولاً؟', O, 104)]),
]
