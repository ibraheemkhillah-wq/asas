"""BMW 3 Series 2027: EV cheaper than petrol (global news, dark theme)."""
# O, Wh, LOGONAVY are provided by news_carousel when the story is loaded.

NAME = "bmw-3series"
THEME = "dark"
BG_DIR = "."
NB = ' '
SLIDES = [
    dict(kind='cover', bg='bmw-1-cover.jpg', stack=[
        ('بي إم دبليو الفئة الثالثة 2027', LOGONAVY, Wh, 60),
        ('الكهربائية أرخص من البنزين', Wh, LOGONAVY, 80),
        ('بفارق 4,400 دولار', O, LOGONAVY, 72)]),
    dict(kind='inner', bg='bmw-2-prices.jpg', chip='الأسعار',
         title=[('الكهربائية أرخص بفارق', Wh), ('4,400 دولار', O)],
         body=[('تبدأ نسخة', Wh), (f'i3{NB}50{NB}xDrive', O), ('الكهربائية من', Wh), ('61,500 دولار،', O),
               ('مقابل', Wh), ('65,900 دولار', O), ('لنسخة البنزين', Wh), (f'M350{NB}xDrive،', O),
               ('ودون رسوم الشحن والتسليم.', Wh)]),
    dict(kind='inner', bg='bmw-3-charging.jpg', chip='المدى والشحن',
         title=[('468 ميلاً', O), ('بشحنة واحدة', Wh)],
         body=[('تصل', Wh), ('i3', O), ('الكهربائية إلى مدى', Wh), ('468 ميلاً', O), ('وفق أرقام بي إم دبليو، ويمكنها استعادة', Wh),
               ('208 أميال', O), ('من المدى خلال', Wh), ('10 دقائق', O), ('فقط من الشحن السريع.', Wh)]),
    dict(kind='inner', bg='bmw-4-market.jpg', chip='السوق', source='المصدر: تك كرانش',
         title=[('الكهربائية', Wh), ('تنافس البنزين', O), ('بالسعر', Wh)],
         body=[('تعتمد النسختان على منصتين مختلفتين. ويأتي ذلك مع استمرار انخفاض أسعار السيارات الكهربائية واقترابها من منافسة البنزين في', Wh),
               ('سعر الشراء الأولي،', O), ('وليس فقط في تكلفة التشغيل والملكية.', Wh)]),
    dict(kind='poll', bg='bmw-5-poll.jpg', chip='شاركنا رأيك', q1='لو الفرق 4,400 دولار...', q2='شو بتختار؟',
         options=[('كهربائية', 'bolt', O, 815), ('بنزين', 'drop', Wh, 262)], tag_y=950,
         cta='جاوبنا بالتعليقات'),
]

