# -*- coding: utf-8 -*-

{
    'name': u'Audoune -- CRM',
    'version': '1.0',
    'summary': u'',
    'category': 'Gestion des opportunités',
    'author': 'Osisoftware',
    'website': '',
    'depends': [
        'base', 'crm'
    ],
    'data': [
        'data/data.xml',
        'security/groups.xml',
        'views/crm_views.xml',
        'views/activity_wizard.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
