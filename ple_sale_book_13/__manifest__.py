# -*- coding: utf-8 -*-
{
    'name': 'Reporte PLE Ventas',
    'version': '13.0.1.1.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'Perú Localización - Reportes Ventas',
    'description': """
    Crea el menú PLE y además crea el libro electrónico de Ventas conla opción de generarlo Detallado por comprobante o Agrupado
    """,
    'depends': [
        'account_origin_invoice',
        'dua_in_invoice',
        'account_exchange_currency',
        'l10n_pe'
    ],
    'data': [
        'data/account_tax_report_line.xml',
        'security/ir_rule.xml',
        'views/base_views.xml',
        'views/account_views.xml',
        'views/move_views.xml',
        'views/ple_sale_views.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
    'auto_install': False,
}
