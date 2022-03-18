# coding: utf-8

from lxml import etree
from odoo import api, models, fields
import json


class ResPartner(models.Model):
    _inherit = 'res.partner'

    inv_document_type_id = fields.Many2one(
        comodel_name='invoice.document.type',
        string='Documento de compra por defecto'
    )

    @api.onchange('supplier_rank')
    def _onchange_supplier_inv_document_type_id(self):
        self.inv_document_type_id = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(ResPartner, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            peruvian_company = self.env.company.get_fiscal_country() == self.env.ref('base.pe')
            if peruvian_company:
                return res
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='inv_document_type_id']"):
                modifiers = json.loads(node.get("modifiers") or '{}')
                modifiers['invisible'] = 1
                node.set("modifiers", json.dumps(modifiers))
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
