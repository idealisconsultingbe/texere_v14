# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ReceptionFormAction(models.Model):
    _name = 'reception.form.action'
    _description = 'Release and Reception Form Actions'
    _check_company_auto = True

    sequence = fields.Integer('Sequence')
    form_type = fields.Selection(selection=[('rc_without_qc', 'RC Without QC'), ('rc_with_qc', 'RC With QC'), ('qc_result', 'QC Results')], string='Type', required=True, copy=True)
    action = fields.Selection(selection=[('lock', 'Lock'), ('notify', 'Notify')], string='Action', required=True, copy=True)
    form_state = fields.Selection(selection=[('confirmed', 'Confirmed'), ('sent', 'Sent'), ('approved', 'Approved'), ('closed', 'Closed')], string='Status', required=True, copy=True)
    picking_type_id = fields.Many2one('stock.picking.type', string='Operation Type', domain="[('company_id', '=', company_id)]", check_compant=True, copy=True)
    group_id = fields.Many2one('res.groups', string='Access Group', copy=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company, copy=True)

    @api.constrains('form_type', 'action', 'form_state', 'picking_type_id', 'group_id', 'company_id')
    def _check_action_unicity(self):
        for action in self:
            if self.env['reception.form.action'].search([('form_type', '=', action.form_type),
                                                         ('action', '=', action.action),
                                                         ('form_state', '=', action.form_state),
                                                         ('picking_type_id', '=', action.picking_type_id.id),
                                                         ('group_id', '=', action.group_id.id),
                                                         ('company_id', '=', action.company_id.id),
                                                         ('id', '!=', action.id)]):
                raise ValidationError(_('Action combination must be unique, please try to change one parameter.'))
