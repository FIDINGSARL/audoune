# -*- coding: utf-8 -*-

{
    'name': u'Audoune -- Ventes',
    'version': '1.0',
    'summary': u'',
    'category': 'Gestion Commerciale',
    'author': 'Osisoftware',
    'website': '',
    'depends': [
        'base', 'stock', 'sale', 'sale_stock', 'product_extend'
    ],
    'data': [
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        # 'report/report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
