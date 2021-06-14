# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class Picking(models.Model):
    _inherit = 'stock.picking'

    count_lots_to_send = fields.Integer(string='Lots to Send', compute='_compute_count_lots_to_send', store=True, tracking=True)
    count_lots_to_process = fields.Integer(string='Lots to Process', compute='_compute_count_lots_to_process', store=True, tracking=True)
    count_lots_to_validate = fields.Integer(string='Lots to Validate', compute='_compute_count_lots_to_validate', store=True, tracking=True)
    count_lots_message = fields.Char(string='Warning Lots Message', compute='_compute_count_lots_to_process', store=True)

    @api.depends('move_line_ids.lot_id.form_to_validate_count', 'check_ids')
    def _compute_count_lots_to_validate(self):
        for pick in self:
            pick.count_lots_to_validate = len(pick.move_line_ids.mapped('lot_id').filtered(lambda lot: lot.form_to_validate_count > 0))

    @api.depends('move_line_ids.lot_id.form_to_send_count')
    def _compute_count_lots_to_send(self):
        for pick in self:
            pick.count_lots_to_send = len(pick.move_line_ids.mapped('lot_id').filtered(lambda lot: lot.form_to_send_count > 0))

    @api.depends('move_line_ids.lot_id.reception_form_count', 'move_line_ids.state')
    def _compute_count_lots_to_process(self):
        for pick in self:
            done_move_lines = pick.move_line_ids.filtered(lambda ml: ml.state == 'done')
            count_lots_to_process = len(done_move_lines.mapped('lot_id').filtered(lambda lot: lot.is_form_mandatory and lot.reception_form_count == 0))
            pick.count_lots_message = _('Do not forget to create the Release and Reception Forms.') if count_lots_to_process else False
            pick.count_lots_to_process = count_lots_to_process

    def open_create_reception_form(self):
        self.ensure_one()
        action = self.env.ref('reception_and_release_management.action_create_reception_form').read()[0]
        if self.env.context.get('form_validation'):
            lots = self.move_line_ids.mapped('lot_id').filtered(lambda lot: lot.form_to_validate_count > 0)
        else:
            done_move_lines = self.move_line_ids.filtered(lambda ml: ml.state == 'done')
            lots = done_move_lines.mapped('lot_id').filtered(lambda lot: lot.is_form_mandatory and lot.reception_form_count == 0)
        action.update({
            'context': {
                'default_picking_id': self.id,
                'default_all_lot_ids': lots.ids,
                'default_available_lot_ids': lots.filtered(lambda lot: lot.product_critical_level in ['furniture', 'less_critical', 'intermediary']).ids,
                'default_hide_edition_fields': self.env.context.get('form_validation')
            },
            'views': [(self.env.ref('reception_and_release_management.create_reception_form_view_form').id, 'form')]
        })
        return action

    def action_view_lots(self):
        """ Action used on button box to open lots to process or to validate """
        action = self.env.ref('stock.action_production_lot_form')
        result = action.read()[0]
        if self.env.context.get('show_lots_to_validate'):
            lot_ids = self.move_line_ids.mapped('lot_id').filtered(lambda lot: lot.form_to_validate_count > 0).ids
        else:
            done_move_lines = self.move_line_ids.filtered(lambda ml: ml.state == 'done')
            lot_ids = done_move_lines.mapped('lot_id').filtered(lambda lot: lot.is_form_mandatory and lot.reception_form_count == 0).ids
        result['domain'] = "[('id', 'in', " + str(lot_ids) + ")]"
        return result

    def button_validate(self):
        for picking in self.filtered(lambda pick: pick.move_line_ids.mapped('lot_id') if pick.move_line_ids else False):
            for form in picking.move_line_ids.mapped('lot_id.reception_form_ids'):
                if self.env['reception.form.action'].search([('action', '=', 'lock'),
                                                             ('form_type', '=', form.type),
                                                             ('form_state', '=', form.state),
                                                             ('picking_type_id', '=', picking.picking_type_id.id),
                                                             ('company_id', '=', form.company_id.id)]):
                    raise UserError(_('Operation type {} is locked for {} in {} state (picking: {}, lot: {}, form: {}). \n\nYou should either cancel this move line or ask your QA to change {} form status.')
                                    .format(picking.picking_type_id.display_name, form.type, form.state, picking.name, form.lot_id.name, form.name, form.name))
        return super().button_validate()



