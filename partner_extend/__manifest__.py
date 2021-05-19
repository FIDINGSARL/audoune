# -*- coding: utf-8 -*-

{
    "name": u"Ajout champs divers dans la fiche partenaire",
    "version": "14.0",
    "depends": ['base', 'account_tres_pec', 'account_tres_customer', 'product_extend', 'sale_extend', 'journal_nblk'],
    "author": "Andema",
    "summary": "IF, RC, CNSS, ICE, TP, ...",
    'website': 'http://www.andemaconsulting.com',
    "category": "BASE",
    "description": "Ajouter des infos sup",
    "init_xml": [],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/rules.xml',
        'security/rules.xml',
        'views/account_move_views.xml',
        'views/partner_extend_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}
