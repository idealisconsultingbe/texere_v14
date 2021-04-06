# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    critical_level = fields.Selection([('furniture', 'Office Furniture'), ('less_critical', 'Less Critical'), ('intermediary', 'Intermediary'), ('critical', 'Critical'), ('femoral', 'Femoral Head')], default='furniture', string='Critical Level')
