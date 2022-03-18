# coding: utf-8

from lxml import etree
from odoo import api, models, fields
from odoo.exceptions import ValidationError
import json

type_validation = [
    ('numbers', 'Numérico'),
    ('letters', 'Alfanumérico'),
    ('no_validation', 'Sin validación')
]

length_validation = [
    ('equal', 'Igual'),
    ('max', 'Hasta'),
    ('no_validation', 'Sin validación')
]


def fields_invisible_per_country(self, fields, res):
    peruvian_company = self.env.company.get_fiscal_country() == self.env.ref('base.pe')
    if peruvian_company:
        return res
    doc = etree.XML(res['arch'])
    for field in fields:
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


def _validate_long(word, length, validation_type, field_name):
    if word and validation_type:
        if validation_type == 'equal':
            if len(word) != length:
                return "- La cantidad de caracteres para el campo '%s' debe ser: %d \n" % \
                       (field_name, length)
        elif validation_type == 'max':
            if len(word) > length:
                return "- La cantidad de caracteres para el campo '%s' debe ser como máximo: %d \n" % \
                       (field_name, length)
    return ''


def _validate_word_structure(word, validation_type, field_name):
    special_characters = '-°%&=~\\+?*^$()[]{}|@%#"/¡¿!:.,;'
    if word:
        if validation_type == 'numbers':
            if not word.isdigit():
                return "- El campo '%s' solo debe contener números.\n" % field_name
            else:
                total = 0
                for d in str(word):
                    total += int(d)
                if total == 0:
                    return "- El campo '%s' no puede contener solo ceros.\n" % field_name
        special = ''
        for letter in word:
            if letter in special_characters:
                special += letter
        if special != '':
            return "- El campo '%s' contiene caracteres no permitidos:  %s \n" % (field_name, special)
    return ''


class InvoiceDocumentType(models.Model):
    _name = 'invoice.document.type'
    _description = "Tipo de documento de venta/compra"

    name = fields.Char(
        string='Nombre',
        required=True
    )
    code = fields.Char(
        string='Código'
    )
    is_active = fields.Boolean(
        string='Activo',
        default=True
    )
    is_sale = fields.Boolean(
        string='Venta'
    )
    is_purchase = fields.Boolean(
        string='Compra'
    )
    prefix_long = fields.Integer(
        string='Longitud Serie'
    )
    prefix_length_validation = fields.Selection(
        selection=length_validation,
        string='Validacion Longitud Serie',
        default='no_validation'
    )
    prefix_validation = fields.Selection(
        selection=type_validation,
        string='Validación Serie',
        default='no_validation'
    )
    correlative_long = fields.Integer(
        string='Longitud Correlativo'
    )
    correlative_length_validation = fields.Selection(
        selection=length_validation,
        string='Validación Longitud Correlativo',
        default='no_validation'
    )
    correlative_validation = fields.Selection(
        selection=type_validation,
        string='Validación Correlativo',
        default='no_validation'
    )
    journal_purchase_id = fields.Many2one(
        comodel_name='account.journal',
        string='Diario'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        default=lambda self: self.env.user.company_id
    )


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    invoice_document_type_id = fields.Many2one(
        comodel_name='invoice.document.type',
        string='Tipo de documento de venta',
        domain="[('is_active', '=', True), ('is_sale', '=', True), ('company_id', '=', company_id)]",
        help="El Tipo de documento en este campo se utilizará en la facturación electrónica"
    )

    @api.onchange('type')
    def _onchange_type(self):
        self.invoice_document_type_id = False


class AccountMove(models.Model):
    _inherit = 'account.move'

    inv_document_type_id = fields.Many2one(
        comodel_name='invoice.document.type',
        string='Tipo de documento'
    )
    error_dialog = fields.Text(
        #compute="_compute_error_dialog",
        store=True,
        help='Campo usado para mostrar mensaje de alerta en el mismo formulario'
    )
    prefix_val = fields.Char(
        string='Serie'
    )
    suffix_val = fields.Char(
        string='Correlativo'
    )
    sunat_code = fields.Char(
        related='inv_document_type_id.code',
        string='Código Sunat'
    )


class UomCategory(models.Model):
    _inherit = 'uom.category'

    name_sunat = fields.Char(
        string='Unidad de medida SUNAT'
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(UomCategory, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            fields = ['name_sunat']
            res = fields_invisible_per_country(self, fields, res)
        return res
