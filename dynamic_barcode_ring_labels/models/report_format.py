# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

from odoo import models, fields


class RReportPaperformat(models.Model):
    _inherit = "report.paperformat"
    rcustom_report = fields.Boolean('Temp Formats', default=False)
