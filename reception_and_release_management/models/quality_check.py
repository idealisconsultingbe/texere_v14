# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    parent_form_id = fields.Many2one('stock.production.lot.reception.form', string='Parent Reception Form', compute='_compute_qc_info', store=True)
    child_form_id = fields.One2many('stock.production.lot.reception.form', 'check_id', string='Child Reception Form', readonly=True, domain=[('type', '=', 'qc_result')])
    show_warning_message = fields.Boolean(string='Warning Message', compute='_compute_show_warning_message')

    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='parent_form_id.lot_id.product_uom_id')
    qty_tested = fields.Float(string='Tested Quantity', digits='Product Unit of Measure', compute='_compute_qc_info', store=True)
    qty_conform = fields.Float(string='Conformed Quantity', digits='Product Unit of Measure')
    qty_not_conform = fields.Float(string='Not Conformed Quantity', digits='Product Unit of Measure')
    qc_reconciliation_consistency = fields.Selection([('consistent', 'Consistent'), ('not_consistent', 'Not consistent')],
                                                  string='Reconciliation Consistency',
                                                  help='Consistency of the tested quantities with the sum of conformed and not conformed quantities')
    qc_reconciliation_comment = fields.Text(string='Reconciliation Comment',
                                         help='Reasons why tested quantities are not consistent with the sum of conformed and not conformed quantities')
    not_conform_fate = fields.Selection([('destroy', 'Destroyed'), ('other', 'Other')], string='Fate of Not Conform')
    not_conform_custom_fate = fields.Char(string='Custom Fate')
    final_packaging_size = fields.Char(string='Final Packaging Size')

    def _compute_show_warning_message(self):
        for check in self:
            check.show_warning_message = False
            if check.picking_id and check.product_id.categ_id.critical_level == 'critical' and not check.picking_id.move_line_ids:
                check.show_warning_message = True

    @api.depends('picking_id.move_line_ids',
                 'picking_id.move_line_ids.product_id',
                 'picking_id.move_line_ids.product_uom_id',
                 'picking_id.move_line_ids.qty_done',
                 'picking_id.move_line_ids.lot_id')
    def _compute_qc_info(self):
        for check in self:
            qty_tested = 0.0
            parent_form_id = False

            if check.product_id.categ_id.critical_level == 'critical' and check.picking_id and check.picking_id.move_line_ids:
                sml_candidates = check.picking_id.move_line_ids.filtered(lambda line: line.product_id == check.product_id and line.lot_id
                                                                                      and line.lot_id.reception_form_ids and 'rc_with_qc' in line.lot_id.reception_form_ids.mapped('type'))
                # at this point, we should have only SMLs with:
                # - the same lot (because of constraints on stock.picking)
                # - the same parent form (because we have the same lot and it is not possible to have more than one parent per lot)
                # There are many reasons why we could have no candidates or candidates with different lot/parent form:
                # - no SMLs with critical products, parent form missing, more than one parent form, SMLs with same critical product but different lot, etc.
                # It is not possible to handle each case. It is a typical 'shit in, shit out' case. Without a unique parent form, we can't create a child form.

                parent_form_candidates = sml_candidates.mapped('lot_id.reception_form_ids').filtered(lambda form: form.type == 'rc_with_qc')
                if len(parent_form_candidates) == 1:
                    parent_form_id = parent_form_candidates
                    qty_tested = sum(sml_candidates.mapped('qty_done'))

            check.qty_tested = qty_tested
            check.parent_form_id = parent_form_id

    @api.onchange('qc_reconciliation_consistency')
    def _onchange_reconciliation_comment(self):
        if self.qc_reconciliation_consistency == 'consistent':
            self.qc_reconciliation_comment = ''

    def write(self, vals):
        fields = ['qty_tested', 'qty_conform', 'qty_not_conform', 'qc_reconciliation_consistency', 'qc_reconciliation_comment', 'not_conform_fate', 'not_conform_custom_fate', 'final_packaging_size']
        if self.child_form_id and self.picking_id:
            form = self.child_form_id[0]
            for field in fields:
                if field in vals and vals[field] != getattr(form, field, False):
                    self.picking_id.activity_schedule(act_type_xmlid='mail.mail_activity_data_warning',
                                   date_deadline=fields.Date.today(),
                                   summary='Quality check info have changed',
                                   note=_('Information on quality check ({}) are no longer consistent with those on QC Results form {}.').format(
                                       f'<a href=# data-oe-model={self._name} data-oe-id={self.id}>{self.name}</a>\n',
                                       f'<a href=# data-oe-model={form._name} data-oe-id={form.id}>{form.name}</a>\n'),
                                   user_id=self.env.uid)
        return super().write(vals)

    def do_pass(self):
        try:
            self._check_form_to_process()
            if self.point_id.is_form_validation_required:
                self._check_form_validation()
        except UserError as e:
            return self._raise_custom_warning(e, _('Unable to process Quality Checks'))

        self._create_child_reception_form()
        return super(QualityCheck, self).do_pass()

    def do_fail(self):
        try:
            self._check_form_to_process()
            if self.point_id.is_form_validation_required:
                self._check_form_validation()
        except UserError as e:
            return self._raise_custom_warning(e, _('Unable to process Quality Checks'))

        self._create_child_reception_form()
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

    def _prepare_child_form_values(self):
        self.ensure_one()
        vals = {
            'type': 'qc_result',
            'check_id': self.id,
            'parent_id': self.parent_form_id.id or False,
            'tested_on': fields.Datetime.now(),
            'tested_by': self.env.user.id,
            'qty_tested': self.qty_tested,
            'qty_conform': self.qty_conform,
            'qty_not_conform': self.qty_not_conform,
            'qc_reconciliation_consistency': self.qc_reconciliation_consistency,
            'qc_reconciliation_comment': self.qc_reconciliation_comment,
            'not_conform_fate': self.not_conform_fate,
            'not_conform_custom_fate': self.not_conform_custom_fate,
            'final_packaging_size': self.final_packaging_size,

            'state': 'confirmed',
            'picking_id': self.picking_id.id or False,
            'lot_id': self.parent_form_id.lot_id.id or False,
            'specification_reference': self.parent_form_id.specification_reference or False,
            'storage_temperature': self.parent_form_id.storage_temperature or False,
            'items_stored': self.parent_form_id.items_stored or False,
            'storage_location': self.parent_form_id.storage_location or False,
            'company_id': self.parent_form_id.company_id.id or self.env.company.id,
        }
        return vals

    def _create_child_reception_form(self):
        # quarantine_zones = self.env['stock.location'].search([('quarantine_zone', '=', True)])
        # quant = self.env['stock.quant'].search([('lot_id', '=', form.lot_id.id),
        #                                         ('location_id', 'in', quarantine_zones.ids)])
        # if len(quant) == 1 and (quant.inventory_quantity - form.qty_tested) <= 0:
        for check in self:
            if check.product_id.categ_id.critical_level == 'critical' and check.parent_form_id and check.picking_id and not check.child_form_id:
                vals = check._prepare_child_form_values()
                form = self.env['stock.production.lot.reception.form'].create(vals)
                form.with_context(send_form=True).send_form()

                if float_compare(sum(check.parent_form_id.child_ids.mapped('qty_tested')),
                                 check.parent_form_id.product_qty, precision_digits=3) >= 0:
                    form.last_child = True

                # chatter notification
                body = _('A QC result form has been created: {}').format(f'<a href=# data-oe-model={form._name} data-oe-id={form.id}>{form.name}</a>\n')
                check.picking_id.message_post(body=body)
