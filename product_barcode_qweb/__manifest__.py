# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

{
    'name': 'Barcode Labels (3 Labels/Page) (Product / Template / Purchase / Picking)',
    'version': '13.0.1.0',
    'category': 'product',
    'summary': 'Zebra Labels | Product Labels | Product Barcode | Gk420 | Barcode Labels | Dynamic Width | 3 Labels per Page',
    'description': """Print Barcode label for products""",
    'author': 'TidyWay',
    'website': 'http://www.tidyway.in',
    #'depends': ['product', 'purchase', 'stock', 'mrp'],
    'depends': ['product', 'purchase', 'stock'],
    'data': [
        'security/barcode_label_security.xml',
        'security/ir.model.access.csv',
        'data/barcode_config.xml',
        'wizard/barcode_labels.xml',
        'views/report_paperformat.xml',
        'views/barcode_config_view.xml',
        'views/report_product_barcode.xml',
        'views/menu_view.xml'
    ],
    'price': 50,
    'currency': 'EUR',
    'installable': True,
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'images': ['images/label.jpg'],
}
