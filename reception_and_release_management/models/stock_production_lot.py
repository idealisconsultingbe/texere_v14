# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    product_critical_level = fields.Selection(related='product_id.categ_id.critical_level', string='Product Critical Level')

    reception_form_ids = fields.One2many('stock.production.lot.reception.form', 'lot_id', string='Reception Forms')
    reception_form_count = fields.Integer(string='Reception Form Count', compute='_compute_form_count', store=True)
    form_to_validate_count = fields.Integer(string='Waiting for Validation Form Count', compute='_compute_form_count', store=True)
    form_to_send_count = fields.Integer(string='Form to Send Count', compute='_compute_form_count', store=True)
    is_form_mandatory = fields.Boolean(string='Form Creation Mandatory', compute='_compute_is_form_mandatory', store=True)

    @api.depends('product_id.categ_id.critical_level')
    def _compute_is_form_mandatory(self):
        for lot in self:
            lot.is_form_mandatory = lot.product_id.categ_id.critical_level in ['less_critical', 'intermediary', 'critical', 'femoral']

    @api.depends('reception_form_ids', 'reception_form_ids.state')
    def _compute_form_count(self):
        form_data = self.env['stock.production.lot.reception.form'].read_group([('lot_id', 'in', self.ids), ('state', '=', 'sent')], ['lot_id'], ['lot_id'])
        forms_to_validate = dict((data['lot_id'][0], data['lot_id_count']) for data in form_data)

        form_data = self.env['stock.production.lot.reception.form'].read_group([('lot_id', 'in', self.ids), ('state', '!=', 'draft')], ['lot_id'], ['lot_id'])
        forms = dict((data['lot_id'][0], data['lot_id_count']) for data in form_data)

        form_data = self.env['stock.production.lot.reception.form'].read_group([('lot_id', 'in', self.ids), ('state', '=', 'confirmed')], ['lot_id'], ['lot_id'])
        forms_to_send = dict((data['lot_id'][0], data['lot_id_count']) for data in form_data)

        for lot in self:
            lot.form_to_validate_count = forms_to_validate.get(lot.id, 0)
            lot.reception_form_count = forms.get(lot.id, 0)
            lot.form_to_send_count = forms_to_send.get(lot.id, 0)

    @api.constrains('reception_form_ids')
    def _check_forms(self):
        for lot in self:
            if lot.reception_form_ids and len(lot.reception_form_ids.filtered(lambda rr: rr.type == 'rc_with_qc')) > 1:
                raise UserError(_('Lot should have only one RC with QC (lot: {}).').format(lot.name))
            if lot.reception_form_ids and lot.reception_form_ids.filtered(lambda rr: rr.type == 'qc_result') and not lot.reception_form_ids.filtered(lambda rr: rr.type == 'rc_with_qc'):
                raise UserError(_('Lot with QC results should have a RC with QC (lot: {}).').format(lot.name))

    def action_view_reception_forms(self):
        """ Action used on button box to open forms """
        action = self.env.ref('reception_and_release_management.action_reception_form')
        result = action.read()[0]
        result['domain'] = "[('lot_id', '=', " + str(self.id) + ")]"
        return result
