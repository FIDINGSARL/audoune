# -*- coding: utf-8 -*-

{
    'name': u'Audoune -- Dossier de rembourssement',
    'version': '1.0',
    'summary': u'',
    'category': 'Gestion de Client',
    'author': 'Osisoftware',
    'website': '',
    'depends': [
        'contacts', 'account_tres_pec'
    ],
    'data': [
        'data/data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/dossier_rembourssement_views.xml',
        'views/partner_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
