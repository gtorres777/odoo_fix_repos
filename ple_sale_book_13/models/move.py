# -*- coding: utf-8 -*-

import json
import pytz
from lxml import etree
from odoo import api, fields, models


def fields_invisible_per_country(self, fields_list, res):
    peruvian_company = self.env.company.get_fiscal_country() == self.env.ref('base.pe')
    if peruvian_company:
        return res
    doc = etree.XML(res['arch'])
    for field in fields_list:
        if isinstance(field, tuple):
            value = "//{}[@name='{}']".format(field[0], field[1])
        else:
            value = "//field[@name='{}']".format(field)
        for node in doc.xpath(value):
            modifiers = json.loads('{}')
            modifiers['invisible'] = 1
            node.set("modifiers", json.dumps(modifiers))
    res['arch'] = etree.tostring(doc, encoding='unicode')
    return res


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    journal_correlative = fields.Selection(
        selection=[
            ('A', 'Apertura'),
            ('C', 'Cierre'),
            ('M', 'Movimiento')
        ],
        default='M',
        string='Estado PLE'
    )
    no_include_ple = fields.Boolean(
        string='No includir en Registro del PLE',
        help="""
Si este campo está marcado, las facturas (documentos de compra y venta), que tengan este diario seteado, no aparecerán en el registro de compras o ventas del PLE. Sin perjuicio de que los asientos contables que dichas facturas generen, aparecerán en los libros que se elaboren con base a los asientos contables, como son el Libro Diario y Mayor.
"""
    )


class AccountMove(models.Model):
    _inherit = 'account.move'

    ple_state = fields.Selection(
        selection=[
            ('0', '0'),
            ('1', '1'),
            ('2', '2'),
            ('6', '6'),
            ('7', '7'),
            ('8', '8'),
            ('9', '9'),
        ],
        string='Estado PLE'
    )
    its_declared = fields.Boolean(
        string='Declarado?'
    )
    date_ple = fields.Date(
        string='Fecha PLE',
        help='Esta fecha sirve para decidir en qué periodo del PLE se presentará esta factura en el registro de compras'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountMove, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            fields_list = [('group', 'ple_group')]
            res = fields_invisible_per_country(self, fields_list, res)
        return res

    @api.onchange('date')
    def onchange_date_ple_from_date(self):
        self.date_ple = self.date

    @api.onchange('invoice_date')
    def onchange_date_ple_from_invoice_date(self):
        self.date_ple = self.invoice_date

    @api.model
    def _convert_date_timezone(self, date_order, format_time='%Y-%m-%d %H:%M:%S'):
        user_tz = pytz.timezone(self.env.user.tz) if self.env.user.tz else pytz.utc
        date_tz = pytz.utc.localize(date_order).astimezone(user_tz)
        date_order = date_tz.strftime(format_time)
        return date_order

    @api.model_create_multi
    def create(self, values):
        for vals in values:
            if vals.get('date') and not vals.get('date_ple'):
                vals['date_ple'] = vals['date']
        obj = super(AccountMove, self).create(values)
        obj.update_correlative()
        return obj

    def write(self, values):
        for rec in self:
            rec.update_cancel_ple_state(values)
            rec.update_correlative()
        return super(AccountMove, self).write(values)

    def update_correlative(self):
        for obj in self:
            prefix = obj.get_type_contributor()
            i = 1
            for line in obj.line_ids:
                line.correlative = '{}{}'.format(prefix, str(i).zfill(9))
                i += 1

    def update_cancel_ple_state(self, values):
        self.ensure_one()
        invoice_document_type_id = self.journal_id.invoice_document_type_id
        if self.type in ['out_invoice', 'out_refund'] and invoice_document_type_id and invoice_document_type_id.code in ['01', '03']:
            if values.get('state') and values['state'] == 'cancel':
                values['ple_state'] = '2'
        return values

    def get_type_contributor(self):
        self.ensure_one()
        new_name = self.journal_id.journal_correlative or ''
        return new_name


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    correlative = fields.Char(
        string='Correlativo'
    )
