# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import models, api, fields


class BarcodeRingConfiguration(models.Model):
    _name = 'barcode.ring.configuration'
    _description = "barcode.ring.configuration"

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

    label_width = fields.Integer(
         'Label Width(MM)',
         required=True,
         help="Page Width",
         default=80
         )
    label_height = fields.Integer(
         'Label Height(MM)',
         required=True,
         help="Page Height",
         default=10
         )
    margin_top = fields.Integer(string="Margin(Top)", required=True)
    margin_bottom = fields.Integer(string="Margin(Bottom)", required=True)
    margin_left = fields.Integer(string="Margin(Left)", required=True)
    margin_right = fields.Integer(string="Margin(Right)", required=True)
    dpi = fields.Integer(string="DPI", required=True)
    header_spacing = fields.Integer(string="Header Spacing", required=True)
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
         default='before')

    left_column_size = fields.Integer(
         string="Left Column Size(pixel)",
         required=True,
         default=132,#36mm
         help="Blank Left Margin Column")
    middle_column_size = fields.Integer(
         string="Middle Column Size(pixel)",
         required=True,
         default=85,#22.5mm
         help="Product name, price, code..display into this Column")
    right_column_size = fields.Integer(
         string="Right Column Size(pixel)",
         required=True,
         default=85,#22.5mm
         help="Barcode display into this Column")

    product_name = fields.Boolean('Product Name', default=True)
    product_variant = fields.Boolean('Attributes')
    price_display = fields.Boolean('Price', default=True)
    product_barcode_no = fields.Boolean('Barcode No.')
    product_code = fields.Boolean('Product Default Code')
    lot = fields.Boolean('Production Lot')

    product_name_size = fields.Char('Product Name Font Size', default=7)
    price_display_size = fields.Char('Price Font Size', default=7)
    product_variant_size = fields.Char('Attributes Font Size', default=7)
    product_barcode_no_size = fields.Char('Barcode No. Font Size', default=7)
    product_code_size = fields.Char('ProductCode Font Size', default=7)

    barcode = fields.Boolean('Barcode Label', default=True)
    barcode_type = fields.Selection([
         ('Codabar', 'Codabar'), ('Code11', 'Code11'),
         ('Code128', 'Code128'), ('EAN13', 'EAN13'),
         ('Extended39', 'Extended39'), ('EAN8', 'EAN8'),
         ('Extended93', 'Extended93'), ('USPS_4State', 'USPS_4State'),
         ('I2of5', 'I2of5'), ('UPCA', 'UPCA'),
         ('QR', 'QR')],
            string='Type', required=True)
    barcode_field = fields.Selection('_get_barcode_field', string="Barcode Field")
    display_height = fields.Integer(
        string="Display Height (px)",
        help="This height will required for display barcode in label.",
        default=25)
    display_width = fields.Integer(
       string="Display Width (px)",
       help="This width will required for display barcode in label.",
       default=120)
    barcode_height = fields.Integer(string="Height",  help="BarLines Quality(Height)", default=1400)
    barcode_width = fields.Integer(string="Width",  help="BarLines Quality(Width)", default=1400)
    humanreadable = fields.Boolean()

    @api.onchange('dpi')
    def onchange_dpi(self):
        if self.dpi < 80:
            self.dpi = 80

    def apply(self):
        return True

    @api.model
    def get_config(self):
        return self.env.ref('dynamic_barcode_ring_labels.default_ring_barcode_configuration')