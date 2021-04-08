# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import models, _
from odoo.exceptions import UserError


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    def check_form_validation(self):
        pickings = self.env['stock.picking'].search(
            [('check_ids', 'in', self.ids), ('count_lots_to_validate', '>', 0)])
        if pickings:
            lots_to_validate_count = sum(pickings.mapped('count_lots_to_validate'))
            raise UserError(_(
                'You still have {} Reception and Release form(s) to validate before processing this quality check (see picking(s): {})').format(
                lots_to_validate_count, ', '.join(pickings.mapped('name'))))

    def check_form_to_process(self):
        def get_orig_pickings(move):
            pickings = self.env['stock.picking']
            if move.move_orig_ids:
                for move_orig in move.move_orig_ids:
                    pickings |= get_orig_pickings(move_orig)
                return pickings
            else:
                return move.picking_id

        pickings = self.env['stock.picking']
        for move in self.picking_id.mapped('move_lines'):  # there may be several records (no ensure_one() or iteration)
            pickings |= get_orig_pickings(move)
        if pickings and any(pickings.mapped('count_lots_to_process')):
            lots_to_process_count = sum(pickings.mapped('count_lots_to_process'))
            raise UserError(_(
                'You still have {} Reception and Release form(s) to fill before processing this quality check (see picking(s): {})').format(
                lots_to_process_count, ', '.join(pickings.filtered(lambda p: p.count_lots_to_process > 0).mapped('name'))))

        if pickings and any(pickings.mapped('count_lots_to_send')):
            lots_to_send_count = sum(pickings.mapped('count_lots_to_send'))
            lots_to_send = pickings.mapped('move_line_ids.lot_id').filtered(lambda lot: lot.form_to_send_count > 0)
            raise UserError(_(
                'You still have {} Reception and Release form(s) to send before processing this quality check (see lot(s): {})').format(
                lots_to_send_count, ', '.join(lots_to_send.mapped('name'))))

    def do_pass(self):
        self.check_form_to_process()
        if self.point_id.is_form_validation:
            self.check_form_validation()
        return super(QualityCheck, self).do_pass()

    def do_fail(self):
        self.check_form_to_process()
        if self.point_id.is_form_validation:
            self.check_form_validation()
        return super(QualityCheck, self).do_fail()

    def do_measure(self):
        self.check_form_to_process()
        if self.point_id.is_form_validation:
            self.check_form_validation()
        return super(QualityCheck, self).do_measure()
