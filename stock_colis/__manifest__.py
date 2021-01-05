# -*- coding: utf-8 -*-

{
    'name': u'Audoune -- Gestion de Colis',
    'version': '1.0',
    'summary': u'',
    'category': 'Gestion de Colis',
    'author': 'Osisoftware',
    'website': '',
    'depends': [
        'stock', 'account_tres_customer'
    ],
    'data': [
        'data/sequence.xml',
        'security/groups.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'views/stock_colis_views.xml',
        'views/stock_inventory_views.xml',
        'report/docs_admin_templates.xml',
        'report/report.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
