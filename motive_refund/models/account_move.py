# coding: utf-8

from odoo import api, fields, models


class ReasonCancellationCreditNote(models.Model):
    _name = 'reason.cancellation.credit.debit'
    _description = 'Códigos de Motivo de emisión de nota de crédito electrónica'

    code = fields.Char(
        string='Código',
        required=True
    )
    description = fields.Char(
        string='Descripción',
        required=True
    )

    def name_get(self):
        result = []
        for afectation_type in self:
            result.append((afectation_type.id, "[%s] %s" % (afectation_type.code, afectation_type.description)))
        return result


class AccountMove(models.Model):
    _inherit = 'account.move'

    name_credit_debit = fields.Char(
        string='Nombre'
    )
    reason_cancellation_id = fields.Many2one(
        comodel_name='reason.cancellation.credit.debit',
        string='Seleccione motivo'
    )

    @api.onchange('reason_cancellation_id', 'type')
    def _onchange_reason_cancellation_id(self):
        if self.reason_cancellation_id and self.type in ['out_refund', 'in_refund']:
            self.name_credit_debit = "[%s] %s" % (self.reason_cancellation_id.code, self.reason_cancellation_id.description)


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    reason_cancellation_id = fields.Many2one(
        comodel_name='reason.cancellation.credit.debit',
        string='Seleccione motivo'
    )

    @api.onchange('reason_cancellation_id')
    def _onchange_reason_cancellation_id(self):
        reason = ''
        if self.reason_cancellation_id:
            reason = "[%s] %s" % (self.reason_cancellation_id.code, self.reason_cancellation_id.description)
        self.reason = reason

    def _prepare_default_reversal(self, move):
        r = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        r.update({
            'reason_cancellation_id': self.reason_cancellation_id.id,
            'name_credit_debit': self.reason,
        })
        return r
