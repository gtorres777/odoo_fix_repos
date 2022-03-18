# -*- coding: utf-8 -*-

from odoo import fields, models


class Account(models.Model):
    _inherit = 'account.account'

    date_account = fields.Date(
        string='Fecha de cuenta',
        default=fields.Date.today
    )
    state_account = fields.Selection(selection=[
        ('1', '1'),
        ('8', '8'),
        ('9', '9'),
    ], string='Estado', default='1')
    ple_selection = fields.Selection(
        selection=[],
        string="PLE"
    )
