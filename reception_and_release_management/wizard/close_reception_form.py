# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class CreateReceptionForm(models.TransientModel):
    _name = 'close.reception.form'
    _description = 'Closure of Release and Reception Form Wizard'

    form_id = fields.Many2one('stock.production.lot.reception.form', string='Release and Reception Form', readonly=True, required=True)
    product_qty = fields.Float(related='form_id.product_qty')
    total_qty_tested = fields.Float(related='form_id.total_qty_tested')
    reconciliation_consistency = fields.Selection([('consistent', 'Consistent'), ('not_consistent', 'Not consistent')], string='Reconciliation Consistency', required=True, help='Consistency of the tested quantities according to form quantities')
    reconciliation_comment = fields.Text(string='Reconciliation Comment', help='Reasons why tested quantities are not consistent with quantities set on R&R form')

    @api.onchange('reconciliation_consistency')
    def _onchange_reconciliation_consistency(self):
        if self.reconciliation_consistency != 'not_consistent':
            self.reconciliation_comment = ''

    def close_reception_form(self):
        self.ensure_one()
        self.form_id.write({
            'state': 'closed',
            'closed_by': self.env.user.id,
            'closed_on': fields.Datetime.now(),
            'reconciliation_consistency': self.reconciliation_consistency,
            'reconciliation_comment': self.reconciliation_comment
        })
        self.form_id._post_message(_('Form closed by {} on {}').format(self.form_id.closed_by.name, self.form_id.closed_on))
        return {}
