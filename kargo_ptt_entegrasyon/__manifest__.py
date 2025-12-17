{
    'name': 'PTT Kargo Entegrasyonu',
    'version': '19.0.1.0.0',
    'category': 'Operations/Inventory',
    'summary': 'PTT Kargo ile sipariş gönderimi ve takibi',
    'description': """
    Odoo PTT Kargo Entegrasyonu ile teslimat süreçlerinizi hızlandırın.
    """,
    'author': '7Dimensions',
    'images': ['static/description/cover.png'],
    'depends': ['stock'],
    'data': [
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
