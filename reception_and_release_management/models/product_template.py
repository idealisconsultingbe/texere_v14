# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    specification_ref = fields.Char(string='Specification Reference')
    storage_temperature = fields.Selection([('rt', '+15/+25°C (RT)'), ('2_8', '+2/+8°C'), ('80', '-80°C')], string='Storage Temperature')
