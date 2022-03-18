# -*- coding: utf-8 -*-

from odoo import fields, models
from ..reports.sale_report_excel import SaleReportExcel, SaleReportTxt
import base64


class PleReportSale(models.Model):
    _name = 'ple.report.sale'
    _description = 'Reporte PLE Registro de Ventas'
    _inherits = {'ple.report.base': 'ple_id'}

    ple_id = fields.Many2one(
        comodel_name='ple.report.base',
        auto_join=True,
        ondelete="cascade",
        required=True,
        index=True
    )
    line_ids = fields.One2many(
        comodel_name='ple.report.sale.line',
        inverse_name='ple_report_sale_id',
        string='Líneas'
    )
    txt_filename = fields.Char()
    txt_binary = fields.Binary('Reporte TXT')

    def name_get(self):
        return [(obj.id, '{} - {}'.format(obj.date_start.strftime('%d/%m/%Y'), obj.date_end.strftime('%d/%m/%Y'))) for obj in self]

    def action_rollback(self):
        self.write({'state': 'draft'})
        return True

    def unlink(self):
        unlink_ple_sale = self.env['ple.report.sale']
        unlink_ple_base = self.env['ple.report.base']
        for obj in self:
            if not obj.exists():
                continue
            unlink_ple_base |= obj.ple_id
            unlink_ple_sale |= obj
        res = super(PleReportSale, unlink_ple_sale).unlink()
        unlink_ple_base.unlink()
        return res

    def _get_data_invoice(self, obj_invoice):
        return self.env['ple.report.base']._get_data_invoice(obj_invoice)

    def _get_journal_correlative(self, obj_invoice):
        obj_company = self.company_id
        return self.env['ple.report.base']._get_journal_correlative(obj_company, obj_invoice)

    def _get_data_origin(self, obj_invoice):
        return self.env['ple.report.base']._get_data_origin(obj_invoice)

    def _get_number_origin(self, obj_invoice):
        return self.env['ple.report.base']._get_number_origin(obj_invoice)

    def _refund_amount(self, obj_invoice):
        return self.env['ple.report.base']._refund_amount(obj_invoice)

    def _get_tax(self, obj_invoice):
        values = {
            'S_BASE_EXP': 0.0,
            'S_BASE_OG': 0.0,
            'S_BASE_OGD': 0.0,
            'S_TAX_OG': 0.0,
            'S_TAX_OGD': 0.0,
            'S_BASE_OE': 0.0,
            'S_BASE_OU': 0.0,
            'S_TAX_ISC': 0.0,
            'S_TAX_ICBP': 0.0,
            'S_BASE_IVAP': 0.0,
            'S_TAX_IVAP': 0.0,
            'S_TAX_OTHER': 0.0,
            'AMOUNT_TOTAL': 0.0
        }

        if obj_invoice.state != 'cancel':
            credit_note_id = self.env.ref('l10n_pe_catalog_yaros.invoice_document_type_nota_credito')
            journal_type_code = obj_invoice.journal_id.invoice_document_type_id
            for obj_ml in obj_invoice.line_ids:
                for obj_tag_tax in obj_ml.tag_ids:
                    tax_name = obj_tag_tax.name[1:]
                    if tax_name in values:
                        if obj_invoice.type == 'out_refund' and tax_name in ['S_BASE_OG', 'S_TAX_OG'] and journal_type_code == credit_note_id:
                            amount = abs(obj_ml.balance) * -1
                        else:
                            amount = obj_ml.balance * -1
                        values[tax_name] += amount
                        values['AMOUNT_TOTAL'] += amount
        return values

    def action_generate_report(self):
        self.line_ids.unlink()

        list_invoices = self.env['account.move'].search([
            ('company_id', '=', self.company_id.id),
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('state', 'not in', ['draft']),
            ('journal_id.no_include_ple', '=', False),
            ('journal_id.type', '=', 'sale'),
            ('its_declared', '=', False)
        ])
        for obj_invoice in list_invoices:
            date_due, ple_state, document_type, document_number, customer_name = self._get_data_invoice(obj_invoice)
            origin_date_invoice, origin_document_code, origin_serie, origin_correlative, _ = self._get_data_origin(obj_invoice)

            v = self._get_tax(obj_invoice)
            sum_amount_export = v['S_BASE_EXP']
            sum_amount_untaxed = v['S_BASE_OG']
            sum_discount_tax_base = v['S_BASE_OGD']
            sum_sale_no_gravadas_igv = v['S_TAX_OG']
            sum_discount_igv = v['S_TAX_OGD']
            sum_amount_exonerated = v['S_BASE_OE']
            sum_amount_no_effect = v['S_BASE_OU']
            sum_isc = v['S_TAX_ISC']
            sum_tax_icbp = v['S_TAX_ICBP']
            sum_rice_tax_base = v['S_BASE_IVAP']
            sum_rice_igv = v['S_TAX_IVAP']
            sum_another_taxes = v['S_TAX_OTHER']
            amount_total = v['AMOUNT_TOTAL']

            values = {
                'name': obj_invoice.date.strftime('%Y%m00'),
                'number_origin': self._get_number_origin(obj_invoice),
                'journal_correlative': self._get_journal_correlative(obj_invoice),
                'date_invoice': obj_invoice.invoice_date,
                'date_due': date_due if obj_invoice.sunat_code and obj_invoice.sunat_code == '14' else False,
                'voucher_sunat_code': obj_invoice.sunat_code,
                'series': obj_invoice.prefix_val,
                'correlative': obj_invoice.suffix_val,
                'customer_document_type': document_type,
                'customer_document_number': document_number,
                'customer_name': self.env['ple.report.base'].validate_string(customer_name, 99),

                'amount_export': sum_amount_export,
                'amount_untaxed': sum_amount_untaxed,
                'discount_tax_base': sum_discount_tax_base,
                'sale_no_gravadas_igv': sum_sale_no_gravadas_igv,
                'discount_igv': sum_discount_igv,
                'amount_exonerated': sum_amount_exonerated,
                'amount_no_effect': sum_amount_no_effect,
                'isc': sum_isc,
                'rice_tax_base': sum_rice_tax_base,
                'tax_icbp': sum_tax_icbp,
                'rice_igv': sum_rice_igv,
                'another_taxes': sum_another_taxes,

                'amount_total': amount_total,
                'code_currency': obj_invoice.currency_id.name,
                'currency_rate': round(obj_invoice.exchange_rate, 3),
                'origin_date_invoice': origin_date_invoice,
                'origin_document_code': origin_document_code,
                'origin_serie': origin_serie,
                'origin_correlative': origin_correlative,
                'ple_state': ple_state,
                'invoice_id': obj_invoice.id,
                'ple_report_sale_id': self.id,
            }
            self.env['ple.report.sale.line'].create(values)
        return True

    def action_generate_excel(self):
        list_data = []
        for obj_line in self.line_ids:
            value = {
                'period': obj_line.name,
                'number_origin': obj_line.number_origin,
                'journal_correlative': obj_line.journal_correlative,
                'date_invoice': obj_line.date_invoice and obj_line.date_invoice.strftime('%d/%m/%Y') or '',
                'date_due': obj_line.date_due and obj_line.date_due.strftime('%d/%m/%Y') or '',
                'voucher_sunat_code': obj_line.voucher_sunat_code,
                'voucher_series': obj_line.series,
                'correlative': obj_line.correlative,
                'correlative_end': obj_line.correlative_end,
                'customer_document_type': obj_line.customer_document_type,
                'customer_document_number': obj_line.customer_document_number,
                'customer_name': obj_line.customer_name,
                'amount_export': obj_line.amount_export,
                'amount_untaxed': obj_line.amount_untaxed,
                'discount_tax_base': obj_line.discount_tax_base,
                'sale_no_gravadas_igv': obj_line.sale_no_gravadas_igv,
                'discount_igv': obj_line.discount_igv,
                'amount_exonerated': obj_line.amount_exonerated,
                'amount_no_effect': obj_line.amount_no_effect,
                'isc': obj_line.isc,
                'rice_tax_base': obj_line.rice_tax_base or '',
                'tax_icbp': obj_line.tax_icbp,
                'rice_igv': obj_line.rice_igv or '',
                'another_taxes': obj_line.another_taxes,
                'amount_total': obj_line.amount_total,
                'code_currency': obj_line.code_currency,
                'currency_rate': obj_line.currency_rate,
                'origin_date_invoice': obj_line.origin_date_invoice and obj_line.origin_date_invoice.strftime('%d/%m/%Y') or '',
                'origin_document_code': obj_line.origin_document_code,
                'origin_serie': obj_line.origin_serie,
                'origin_correlative': obj_line.origin_correlative,
                'contract_name': obj_line.contract_name,
                'inconsistency_type_change': obj_line.inconsistency_type_change,
                'payment_voucher': obj_line.payment_voucher,
                'ple_state': obj_line.ple_state
            }
            list_data.append(value)
        sale_report = SaleReportTxt(self, list_data)
        values_content = sale_report.get_content()
        self.txt_binary = base64.b64encode(
            values_content.encode() or '\n'.encode()
        )
        self.txt_filename = sale_report.get_filename()
        if not values_content:
            self.error_dialog = 'No hay contenido para presentar en el registro de ventas electrónicos de este periodo.'
        else:
            self.erro_dialog = ''

        sale_report_xls = SaleReportExcel(self, list_data)
        values_content_xls = sale_report_xls.get_content()
        self.xls_binary = base64.b64encode(values_content_xls)
        self.xls_filename = sale_report_xls.get_filename()
        self.date_ple = fields.Date.today()
        self.state = 'load'
        return True

    def action_close(self):
        self.ensure_one()
        self.write({
            'state': 'closed'
        })
        for obj_line in self.line_ids:
            if obj_line.invoice_id:
                obj_line.invoice_id.its_declared = True
        return True

    def action_rollback(self):
        for obj_line in self.line_ids:
            if obj_line.invoice_id:
                obj_line.invoice_id.its_declared = False
        self.state = 'draft'
        return True


class PleReportSaleLine(models.Model):
    _name = 'ple.report.sale.line'
    _description = 'Reporte PLE Registro de Ventas - Líneas'

    name = fields.Char(
        string='Periodo',
        required=True
    )
    ple_report_sale_id = fields.Many2one(
        comodel_name='ple.report.sale',
        string='Reporte de Venta'
    )
    number_origin = fields.Char(
        string='Número Origen'
    )
    journal_correlative = fields.Char(
        string='Correlativo Asiento'
    )
    date_invoice = fields.Date(
        string='Fecha Contable'
    )
    date_due = fields.Date(
        string='Fecha de Vencimiento'
    )
    voucher_sunat_code = fields.Char(
        string='Tipo de Comprobante'
    )
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Comprobante'
    )
    series = fields.Char(
        string='Series'
    )
    correlative = fields.Char(
        string='Correlativo Inicio'
    )
    correlative_end = fields.Char(
        string='Correlativo Fin'
    )
    customer_document_type = fields.Char(
        string='Tipo Doc. de Identidad'
    )
    customer_document_number = fields.Char(
        string='# Doc. de Identidad'
    )
    customer_name = fields.Char(
        string='Nombre Cliente'
    )
    amount_export = fields.Float(
        string='Valor Facturado de Exportación'
    )
    amount_untaxed = fields.Float(
        string='Operación Gravada'
    )
    discount_tax_base = fields.Float(
        string='Descuento de la base Imponible'
    )
    sale_no_gravadas_igv = fields.Float(
        string='Impuesto General a las Ventas y/o Impuesto de Promoción Municipal'
    )
    discount_igv = fields.Float(
        string='Descuento del Impuesto General a las Ventas'
    )
    amount_exonerated = fields.Float(
        string='Operación Exonerada'
    )
    amount_no_effect = fields.Float(
        string='Operación Inafecta'
    )
    isc = fields.Float(
        string='Impuesto Selectivo al Consumo'
    )
    tax_icbp = fields.Float(
        string='Impuesto consumo de bolsas de plástico'
    )
    rice_tax_base = fields.Float(
        string='Operación con IVA'
    )
    rice_igv = fields.Float(
        string='Impuesto de Operación con IVA'
    )
    another_taxes = fields.Float(
        string='Otros Conceptos, tributos y cargos'
    )
    amount_total = fields.Float(
        string='Total'
    )
    code_currency = fields.Char(
        string='Código de la moneda'
    )
    currency_rate = fields.Float(
        string='Tipo de Cambio',
        digits=(12, 3)
    )
    origin_date_invoice = fields.Date(
        string='Fecha Pago'
    )
    origin_document_code = fields.Char(
        string='Tipo de comprobante'
    )
    origin_serie = fields.Char(
        string='Serie'
    )
    origin_correlative = fields.Char(
        string='Correlativo',
    )
    contract_name = fields.Char(
        string='Identificador de Contrato y/o Proyecto'
    )
    payment_voucher = fields.Integer(
        string='Identificador de comprobante de pago',
        default=1
    )
    inconsistency_type_change = fields.Char(
        string='Inconsistencia tipo de cambio'
    )
    ple_state = fields.Selection(
        selection=[
            ('1', '1'),
            ('2', '2'),
            ('8', '8'),
            ('9', '9'),
        ],
        string='Estado',
        default='1'
    )
