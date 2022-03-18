# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import models, api, fields


class TRBarcodeConfiguration(models.Model):
    _name = 'trbarcode.configuration'
    _description = 'trbarcode.configuration'

    @api.model
    def _get_barcode_field(self):
        field_list = []
        ir_model_id = self.env['ir.model'].search([('model', '=', 'product.product')])
        if ir_model_id:
            for field in self.env['ir.model.fields'].search([
                     ('field_description', '!=', 'unknown'),
                     ('readonly', '=', False),
                     ('model_id', '=', ir_model_id.id),
                     ('ttype', '=', 'char')]):
                field_list.append((field.name, field.field_description))
        return field_list

    page_height = fields.Integer(string="Page Height(mm)", default=22)
    page_width = fields.Integer(string="Page Width(mm)", default=110)
    margin_bottom = fields.Integer(string="Margin(Bottom)", default=1)
    margin_top = fields.Integer(string="Margin(Top)", default=1)
    margin_bottom = fields.Integer(string="Margin(Bottom)", default=1)
    margin_left = fields.Integer(string="Margin(Left)", default=1)
    margin_right = fields.Integer(string="Margin(Right)", default=1)

    first_padding_top = fields.Integer(string="Padding(Top)", default=1)
    first_padding_bottom = fields.Integer(string="Padding(Bottom)", default=1)
    first_padding_left = fields.Integer(string="Padding(Left)", default=1)
    first_padding_right = fields.Integer(string="Padding(Right)", default=1)

    second_padding_top = fields.Integer(string="Padding(Top)", default=1)
    second_padding_bottom = fields.Integer(string="Padding(Bottom)", default=1)
    second_padding_left = fields.Integer(string="Padding(Left)", default=1)
    second_padding_right = fields.Integer(string="Padding(Right)", default=1)

    third_padding_top = fields.Integer(string="Padding(Top)", default=1)
    third_padding_bottom = fields.Integer(string="Padding(Bottom)", default=1)
    third_padding_left = fields.Integer(string="Padding(Left)", default=1)
    third_padding_right = fields.Integer(string="Padding(Right)", default=1)

    currency = fields.Many2one(
           'res.currency',
           string="Currency",
           default=lambda self: self.env.user.company_id.currency_id
           )
    currency_position = fields.Selection([
          ('after', 'After Amount'),
          ('before', 'Before Amount')],
         'Symbol Position',
         help="Determines where the currency symbol"
         " should be placed after or before the amount.",
         default='after')
    barcode_type = fields.Selection([
         ('Codabar', 'Codabar'), ('Code11', 'Code11'),
         ('Code128', 'Code128'), ('EAN13', 'EAN13'),
         ('Extended39', 'Extended39'), ('EAN8', 'EAN8'),
         ('Extended93', 'Extended93'), ('USPS_4State', 'USPS_4State'),
         ('I2of5', 'I2of5'), ('UPCA', 'UPCA'),
         ('QR', 'QR')],
            string='Type', required=True,
            default='EAN13')
    barcode_height = fields.Integer(string="Height",  help="Height of barcode.")
    barcode_width = fields.Integer(string="Width",  help="Width of barcode.")
    barcode_field = fields.Selection('_get_barcode_field', string="Barcode Field")
    display_height = fields.Integer(
        string="Display Height (px)",
        help="This height will required for display barcode in label.")
    display_width = fields.Integer(
       string="Display Width (px)",
       help="This width will required for display barcode in label.")
    humanreadable = fields.Boolean(default=False)

    product_code = fields.Boolean('Product Default Code', default=True)
    product_variant = fields.Boolean('Attributes', default=False)
    product_barcode_no = fields.Boolean('Barcode No.', default=True)
    product_name = fields.Boolean('Product Name', default=True)
    price_display = fields.Boolean('Price')

    product_code_size = fields.Char('ProductCode Font Size', default=10)
    product_variant_size = fields.Char('Attributes Font Size', default=10)
    product_barcode_no_size = fields.Char('Barcode No. Font Size', default=10)
    product_name_size = fields.Char('Product Name Font Size', default=10)
    price_display_size = fields.Char('Price Font Size', default=10)

    def apply(self):
        format = self.env.ref('product_barcode_qweb.paperformat_trbarcode_label')
        if format:
            format.sudo().write({
                          'page_width': self.page_width or 110,
                          'page_height': self.page_height or 22,
                          'margin_top': self.margin_top or 0,
                          'margin_bottom': self.margin_bottom or 0,
                          'margin_left': self.margin_left or 0,
                          'margin_right': self.margin_right or 0,
                          })
        return True

    @api.model
    def get_config(self):
        return self.env.ref('product_barcode_qweb.default_trbarcode_configuration')
