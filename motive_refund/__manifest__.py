# -*- coding: utf-8 -*-
{
    'name': 'Anulación de Factura estructurado',
    'version': '13.0.1.1',
    'author': 'Consultoria Yaroslab',
    'website': 'http://www.yaroslab.com',
    'description': """
    Desde un nuevo objeto permite setear el campo motivo de la nota de credito, desde esta o desde el wizard de la factura.
    """,
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False
}
