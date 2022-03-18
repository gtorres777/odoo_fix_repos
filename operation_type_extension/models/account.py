# coding: utf-8

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    operation_type_id = fields.Many2one(
        comodel_name='operation.type',
        string='Tipo de operación',
        required=True,
        default=lambda self: self.env.ref('operation_type_extension.operation_type_0101', False)
    )


class OperationType(models.Model):
    _name = 'operation.type'
    _description = 'Catálogo SUNAT N° 51'
    _order = 'code asc'

    code = fields.Char(
        string='Código',
        required=True
    )
    operation_description = fields.Char(
        string='Descripción',
        required=True
    )

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, "[%s] %s" % (rec.code or '', rec.operation_description or '')))
        return result
