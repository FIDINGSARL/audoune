# -*- coding: utf-8 -*-

{
    "name": u"Audoune: Chèques",
    "version": "14.0",
    "depends": ['base', 'mail', 'account_tres_customer',
                'account_tres_supplier', 'partner_extend',
                'project_extend'],
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
        'wizard/rejet_cheque_wizard_views.xml',
        'views/supplier_payment_views.xml',
        'views/paiement_record.xml'
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
