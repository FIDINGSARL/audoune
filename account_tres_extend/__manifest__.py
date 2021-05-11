# -*- coding: utf-8 -*-

{
    "name": u"Audoune: Chèques",
    "version": "14.0",
    "depends": ['base', 'account_tres_customer', 'account_tres_supplier'],
    "author": "Osisoftware",
    "summary": "",
    'website': '',
    "category": "",
    "description": "",
    "init_xml": [],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/customer_payment_views.xml',
        'views/supplier_payment_views.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
