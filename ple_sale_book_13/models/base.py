# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    type_contributor = fields.Selection(selection=[
        ('CUO', 'Contribuyentes del Régimen General'),
        ('RER', 'Contribuyentes del Régimen Especial de Renta')
    ], string='Tipo de contribuyente')


class PleReportBase(models.Model):
    _name = 'ple.report.base'
    _description = 'Base libros - PLE'

    date_start = fields.Date(
        string='Fecha Inicio',
        required=True
    )
    state = fields.Selection(selection=[
        ('draft', 'Borrador'),
        ('load', 'Generado'),
        ('closed', 'Declarado')
    ], string='Estado', default='draft', required=True)
    date_end = fields.Date(
        string='Fecha Fin',
        required=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company
    )
    date_ple = fields.Date(
        string='Generado el',
        readonly=True
    )
    state_send = fields.Selection(selection=[
        ('0', 'Cierre de Operaciones - Bajo de Inscripciones en el RUC'),
        ('1', 'Empresa o Entidad Operativa'),
        ('2', 'Cierre de libro - No Obligado a llevarlo')
    ], string='Estado de Envío', required=True)
    xls_filename = fields.Char(string='Filaname .xlsx')
    xls_binary = fields.Binary(string='Reporte Excel')
    error_dialog = fields.Text(readonly=True)
    ple_type = fields.Selection(selection=[
        ('ple_sale', 'Ventas'),
        ('ple_purchase', 'Compras')
    ], string='Tipo PLE', required=True)

    @staticmethod
    def validate_string(word):
        return word

    @staticmethod
    def validate_string(value, length=-1):
        if value:
            if value.find('–') != -1:
                value = value.replace("–", " ")
            if value.find('/') != -1:
                value = value.replace("/", " ")
            if value.find('\n') != -1:
                value = value.replace('\n', ' ')
            if value.find('&') != -1:
                value = value.replace('&', '&amp;')
            if value.find('á') != -1:
                value = value.replace('á', 'a')
            if value.find('é') != -1:
                value = value.replace('é', 'e')
            if value.find('í') != -1:
                value = value.replace('í', 'i')
            if value.find('ó') != -1:
                value = value.replace('ó', 'o')
            if value.find('ú') != -1:
                value = value.replace('ú', 'u')
            if length != -1:
                return value[:length]
        return ''

    @staticmethod
    def check_decimals(value):
        value = str(float('%.2f' % value))
        if not len(value.rsplit('.')[-1]) == 2:
            value += '0'
        return value

    def action_generate_report(self):
        pass

    def action_generate_excel(self):
        pass

    def action_close(self):
        pass

    def action_rollback(self):
        return True

    def _get_number_origin(self, obj_invoice):
        number_origin = obj_invoice.name.replace('/', '').replace('-', '') if obj_invoice.name else ''
        return number_origin

    def _get_data_invoice(self, obj_invoice):
        obj_ple_state = obj_invoice.ple_state
        obj_partner = obj_invoice.partner_id
        if obj_invoice.state != 'cancel':
            return obj_invoice.invoice_date_due, obj_ple_state, obj_partner.l10n_latam_identification_type_id.code, obj_partner.vat, obj_partner.name
        else:
            return False, obj_ple_state, obj_partner.l10n_latam_identification_type_id.code, obj_partner.vat, obj_partner.name

    def _get_journal_correlative(self, obj_company, obj_invoice=False, new_name=''):
        if obj_company.type_contributor == 'CUO':
            if obj_invoice and obj_invoice.line_ids:
                new_name = obj_invoice.line_ids[0].correlative or ''
            if not new_name:
                new_name = 'M000000001'
        elif obj_company.type_contributor == 'RER':
            new_name = 'M-RER'
        return new_name

    def _get_data_origin(self, obj_invoice):
        return obj_invoice.origin_invoice_date, obj_invoice.origin_inv_document_type_id.code, obj_invoice.origin_serie, obj_invoice.origin_correlative, obj_invoice.origin_number.code_aduana

    def unlink(self):
        if self.state == 'closed':
            raise Warning('Regrese a estado borrador para revertir y permitir eliminar.')
        return super(PleReportBase, self).unlink()

    def _refund_amount(self, values):
        for k in values.keys():
            values[k] *= -1
        return values
