# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, _
from odoo.exceptions import UserError


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    def do_pass(self):
        try:
            self._check_form_to_process()
            if self.point_id.is_form_validation_required:
                self._check_form_validation()
        except UserError as e:
            return self._raise_custom_warning(e, _('Unable to process Quality Checks'))
        return super(QualityCheck, self).do_pass()

    def do_fail(self):
        try:
            self._check_form_to_process()
            if self.point_id.is_form_validation_required:
                self._check_form_validation()
        except UserError as e:
            return self._raise_custom_warning(e, _('Unable to process Quality Checks'))
        return super(QualityCheck, self).do_fail()

    def do_measure(self):
        try:
            self._check_form_to_process()
            if self.point_id.is_form_validation_required:
                self._check_form_validation()
        except UserError as e:
            return self._raise_custom_warning(e, _('Unable to process Quality Checks'))
        return super(QualityCheck, self).do_measure()

    def _create_picking_scheduled_activity(self, pickings, reason, records=None):
        for pick in pickings:
            pick.activity_schedule(act_type_xmlid='mail.mail_activity_data_warning',
                                   date_deadline=fields.Date.today(),
                                   summary=' '.join(w.title() for w in reason.split()), # capitalize does not work the way we want with 'R&R' string
                                   note=_('Unable to process quality checks because of {}.').format('%s (%s)' % (reason, records) if records else reason),
                                   user_id=self.env.uid)
            
    def _raise_custom_warning(self, description, reason):
        warning = self.env['reception.form.custom.warning'].create({
            'title': reason,
            'description': description,
        })
        return {
            'name': reason,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'reception.form.custom.warning',
            'res_id': warning.id,
            'target': 'new'
        }

    def _check_form_validation(self):
        pickings = self.env['stock.picking'].search(
            [('check_ids', 'in', self.ids), ('count_lots_to_validate', '>', 0)])
        if pickings:
            forms_to_validate = pickings.mapped('move_line_ids.lot_id.reception_form_ids').filtered(lambda rr: rr.state == 'sent')
            # error raised should be catched in an except block or this transactionnal block won't be persisted
            self._create_picking_scheduled_activity(pickings, _('pending R&R validation'), records=', '.join(forms_to_validate.mapped('name')))
            raise UserError(_(
                'You still have {} Reception and Release form(s) to validate before processing this quality check (see form(s): {})').format(
                len(forms_to_validate), ', '.join(forms_to_validate.mapped('name'))))

    def _check_form_to_process(self):
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
            pickings_with_form_to_process = pickings.filtered(lambda p: p.count_lots_to_process > 0)
            # error raised should be catched in an except block or this transactionnal block won't be persisted
            self._create_picking_scheduled_activity(pickings_with_form_to_process, _('pending R&R to create'))
            raise UserError(_(
                'You still have Reception and Release form(s) to fill before processing this quality check (see picking(s): {})').format(', '.join(pickings_with_form_to_process.mapped('name'))))

        if pickings and any(pickings.mapped('count_lots_to_send')):
            pickings_with_form_to_send = pickings.filtered(lambda p: p.count_lots_to_send > 0)
            forms_to_send = pickings.mapped('move_line_ids.lot_id.reception_form_ids').filtered(lambda rr: rr.state == 'confirmed')
            # error raised should be catched in an except block or this transactionnal block won't be persisted
            self._create_picking_scheduled_activity(pickings_with_form_to_send, _('pending R&R to send'), records=', '.join(forms_to_send.mapped('name')))
            raise UserError(_(
                'You still have {} Reception and Release form(s) to send before processing this quality check (see form(s): {})').format(
                len(forms_to_send), ', '.join(forms_to_send.mapped('name'))))
