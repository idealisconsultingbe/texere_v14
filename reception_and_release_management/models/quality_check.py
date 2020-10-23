# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import models, _
from odoo.exceptions import UserError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    def check_form_validation(self):
        pickings = self.env['stock.picking'].search(
            [('check_ids', '=', self.id), ('count_lots_to_validate', '>', 0)])
        if pickings:
            lots_to_validate_count = sum(pickings.mapped('count_lots_to_validate'))
            raise UserError(_(
                'You still have {} Reception and Release form(s) to validate before processing this quality check (see picking(s): {})').format(
                lots_to_validate_count, ' ,'.join(pickings.mapped('name'))))

    def do_pass(self):
        if self.point_id.is_form_validation:
            self.check_form_validation()
        return super(QualityCheck, self).do_pass()

    def do_fail(self):
        if self.point_id.is_form_validation:
            self.check_form_validation()
        return super(QualityCheck, self).do_fail()

    def do_measure(self):
        if self.point_id.is_form_validation:
            self.check_form_validation()
        return super(QualityCheck, self).do_measure()
