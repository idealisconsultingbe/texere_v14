# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    reception_form_ids = fields.One2many('stock.production.lot.reception.form', 'lot_id', string='Reception Forms')
    reception_form_count = fields.Integer(string='Reception Form Count', compute='_compute_reception_form_count', store=True)
    form_to_validate_count = fields.Integer(string='Waiting for Validation Form Count', compute='_compute_form_to_validate_count', store=True)
    is_form_mandatory = fields.Boolean(string='Form Creation Mandatory', compute='_compute_is_form_mandatory', store=True)

    @api.depends('product_id.categ_id.critical_level')
    def _compute_is_form_mandatory(self):
        for lot in self:
            lot.is_form_mandatory = lot.product_id.categ_id.critical_level in ['less_critical', 'intermediary', 'critical', 'femoral']

    @api.depends('reception_form_ids', 'reception_form_ids.state')
    def _compute_form_to_validate_count(self):
        form_data = self.env['stock.production.lot.reception.form'].read_group([('lot_id', 'in', self.ids), ('state', '=', 'sent')], ['lot_id'], ['lot_id'])
        form = dict((data['lot_id'][0], data['lot_id_count']) for data in form_data)
        for lot in self:
            lot.form_to_validate_count = form.get(lot.id, 0)

    @api.depends('reception_form_ids', 'reception_form_ids.state')
    def _compute_reception_form_count(self):
        form_data = self.env['stock.production.lot.reception.form'].read_group([('lot_id', 'in', self.ids), ('state', '!=', 'draft')], ['lot_id'], ['lot_id'])
        form = dict((data['lot_id'][0], data['lot_id_count']) for data in form_data)
        for lot in self:
            lot.reception_form_count = form.get(lot.id, 0)

    def action_view_reception_forms(self):
        """ Action used on button box to open forms """
        action = self.env.ref('reception_and_release_management.action_reception_form')
        result = action.read()[0]
        result['domain'] = "[('lot_id', '=', " + str(self.id) + ")]"
        return result
