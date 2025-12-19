{
    'name': '7D Yazışmalar (Correspondence Management)',
    'version': '19.0.1.0.2',
    'category': 'Sales/CRM',
    'summary': 'Gelen ve Giden resmi yazışmaların takibi, arşivlenmesi ve yönetimi.',
    'description': """
7D Yazışmalar Modülü
====================
Firmalar arası, departmanlar arası ve kişiler arası resmi yazışmaların (Gelen/Giden)
takibini yapmak için geliştirilmiştir.

Temel Özellikler:
----------------
* Gelen ve Giden yazı kategorizasyonu.
* Yazışma serileri ve otomatik belge numaralandırma.
* Konu ve İçerik için İngilizce/Türkçe desteği.
* İlgi tutulan yazıların (References) listelenmesi.
* Sharepoint ve PDF bağlantı desteği.
    """,
    'author': '7Dimensions',
    'website': 'https://7dimensions.eu',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/correspondence_views.xml',
        'views/correspondence_report.xml',
        'views/menu_views.xml',
    ],
    'application': True,
    'installable': True,
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'EUR',
    'icon': 'static/description/icon.png',
    'images': [
        'static/description/icon.png',
        'static/description/banner.png',
        'static/description/screenshot_1.png',
    ],
}
