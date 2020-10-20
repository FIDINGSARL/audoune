# -*- encoding: utf-8 -*-

{
    'name': 'Gestion des immobilisations (norme Article)',
    'version': '1.0',
    'author': 'Andema',
    'website': 'http://www.andemaconsulting.com',
    "depends": [
        'account','account_asset_comm','stock', 'hr', 'account_asset_ma', 'product'
    ],
    'data': [
        "views/asset.xml",
        "views/product_template.xml",
        "report/asset_report.xml",
        "report/asset_report_templates.xml",
        "report/product_label_templates.xml",
        "report/asset_label_report.xml",
        "wizard/print_asset_report.xml",
        "data/sequence.xml",

        ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
