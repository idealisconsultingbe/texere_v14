# -*- coding: utf-8 -*-
# Part of Idealis. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    quarantine_zone = fields.Boolean(string='Is a Quarantine Zone', default=False)
