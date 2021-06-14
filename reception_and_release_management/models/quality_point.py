# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'quality.point'

    is_form_validation_required = fields.Boolean(string='Form Validation', help='R&R form validation is required before processing quality checks from this control point')

    @api.onchange('product_ids')
    def _onchange_product_ids(self):
        if self.product_ids and self.product_ids[0].categ_id.critical_level in ['intermediary', 'critical', 'femoral']:
            self.is_form_validation_required = True

    @api.onchange('is_form_validation_required')
    def _onchange_is_form_validation_required(self):
        if self.product_ids and self.product_ids[0].categ_id.critical_level in ['intermediary', 'critical', 'femoral'] and not self.is_form_validation_required:
            return {
                'warning': {
                    'title': _('Warning!'),
                    'message': _('Form validation is mandatory for products with intermediary, critical or femoral heads critical levels.')}}

    @api.depends('company_id', 'product_ids')
    def _compute_available_product_ids(self):
        super()._compute_available_product_ids()
        for point in self:
            if point.product_ids:
                point.available_product_ids = point.available_product_ids.filtered(lambda p: p.categ_id.critical_level == point.product_ids[0].categ_id.critical_level)

    @api.constrains('product_ids', 'is_form_validation_required')
    def _check_product_ids(self):
        for record in self:
            if record.product_ids and len(record.product_ids.mapped('categ_id.critical_level')) > 1:
                raise ValidationError(_('It is not possible to have a control point on products with different critical levels.'))
            if record.product_ids and self.product_ids[0].categ_id.critical_level in ['intermediary', 'critical', 'femoral'] and not record.is_form_validation_required:
                raise ValidationError(_('Form validation is mandatory for products with intermediary, critical or femoral heads critical levels.'))
