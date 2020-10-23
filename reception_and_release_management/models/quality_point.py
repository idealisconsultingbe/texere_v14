# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'quality.point'

    is_form_validation = fields.Boolean(string='Form Validation', help='R&R form validation is required before processing quality checks from this control point')
