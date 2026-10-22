"""BMW voluntary severance programme, Oct 2026 (global news, light theme). Images: Canva AI; roundel: BMW AG."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "bmw-exit"
THEME = "light"
SOURCE = "المصدر: هاندلسبلات و BMW Blog"
SLIDES = [
    dict(kind='cover', bg='bmw-exit-1.jpg', mark='bmw-roundel.png', mark_w=120, stack=[
        ('بي إم دبليو تعرض على موظفيها', LOGONAVY, Wh, 60),
        ('أكثر من 730 ألف دولار', Wh, LOGONAVY, 80),
        ('مقابل ترك العمل!', O, LOGONAVY, 72)]),
    dict(kind='inner', bg='bmw-exit-2.jpg', chip='العرض',
         title=[('مغادرة طوعية', Wh), ('بدل التسريح', O)],
         body=[('بدلاً من التسريح المباشر، أطلقت الشركة برنامجاً للمغادرة الطوعية يشمل نحو', Wh), ('40 ألف موظف', O),
               ('من غير عمّال الإنتاج في ألمانيا، بتعويضات تُحسب لكل موظف على حدة، وتجاوزت في بعض الحالات', Wh),
               ('650 ألف يورو،', O), ('مع', Wh), ('مكافأة إضافية', O), ('لمن يغادر مبكراً.', Wh)]),
    dict(kind='inner', bg='bmw-exit-3.jpg', chip='الأسباب',
         title=[('8 آلاف وظيفة', O), ('بحلول 2027', Wh)],
         body=[('تخطط بي إم دبليو لتقليص نحو', Wh), ('8 آلاف وظيفة في ألمانيا', O),
               ('بحلول نهاية 2027، بعد تراجع تسليماتها في الصين بنحو', Wh), ('25%', O),
               ('في الربع الثالث، وسط', Wh), ('منافسة شرسة من الشركات الصينية.', O)]),
    dict(kind='inner', bg='bmw-exit-4.jpg', chip='المفاجأة',
         title=[('البوابة الإلكترونية', Wh), ('توقفت!', O)],
         body=[('مع إطلاق البرنامج، دخل عشرات آلاف الموظفين في وقت واحد للاطلاع على عروضهم، حتى', Wh),
               ('تعطّلت البوابة الداخلية مؤقتاً،', O), ('وأوقفت الشركة لفترة استقبال طلبات جديدة بسبب', Wh),
               ('الإقبال الكبير.', O)]),
    dict(kind='ask', bg='bmw-exit-5.jpg', chip='شاركنا رأيك', top=250, lines=[
        ('هل يكفي خفض التكاليف', LOGONAVY, 64),
        ('وتقليص الوظائف لمواجهة', LOGONAVY, 64),
        ('المنافسة الصينية؟', O, 92)]),
]
