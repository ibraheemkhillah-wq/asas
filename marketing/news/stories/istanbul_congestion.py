"""Istanbul tops the world for time lost in traffic (INRIX 2025 Global Traffic Scorecard), dark theme.
Images: Higgsfield GPT Image (at the user's request)."""
# Bar values are hours minus 80 so the gaps between cities read. O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "istanbul-congestion"
THEME = "dark"
SOURCE = "المصدر: مؤشر INRIX العالمي لحركة المرور 2025"
SLIDES = [
    dict(kind='cover', bg='congest-1-cover.jpg', stack=[
        ('إسطنبول الأولى عالمياً', LOGONAVY, Wh, 64),
        ('في وقت الزحام', Wh, LOGONAVY, 84),
        ('118 ساعة سنوياً على الطريق', O, LOGONAVY, 62)]),
    dict(kind='stats', bg='congest-1-cover.jpg', blur=6, dim=0.45, grade_from=640, rh=104,
         chip='أكثر المدن ازدحاماً في العالم', total='118', total_label='ساعة سنوياً في الزحام', rows=[
            ('إسطنبول', '118', 38), ('شيكاغو', '112', 32), ('مكسيكو سيتي', '108', 28),
            ('نيويورك', '102', 22), ('فيلادلفيا', '101', 21)]),
    dict(kind='inner', bg='congest-3-jam.jpg', chip='للعام الثاني',
         title=[('نحو 5 أيام كاملة', O), ('في الزحام', Wh)],
         body=[('تصدّرت إسطنبول القائمة', Wh), ('للعام الثاني على التوالي،', O),
               ('بعدما ارتفع وقت التأخير فيها بنسبة', Wh), ('12%', O), ('مقارنةً بعام 2024، ليصل إلى', Wh),
               ('118 ساعة', O), ('يقضيها السائق عالقاً في الطريق خلال عام واحد.', Wh)]),
    dict(kind='ask', bg='congest-4-ask.jpg', chip='شاركنا رأيك', top=380, lines=[
        ('كم ساعة تقضي', Wh, 70),
        ('في زحام إسطنبول', Wh, 70),
        ('كل يوم؟', O, 100)]),
]
