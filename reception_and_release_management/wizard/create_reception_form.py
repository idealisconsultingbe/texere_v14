# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class CreateReceptionForm(models.TransientModel):
    _name = 'create.reception.form'
    _description = 'Creation of Release and Reception Form Wizard'

    # @api.model
    # def default_get(self, fields_list):
    #     result = super(CreateReceptionForm, self).default_get(fields_list)
    #     if 'reception_form_id' in result:
    #         reception_form = self.env['stock.production.lot.reception.form'].browse(result['reception_form_id'])
    #         result['packaging_state'] = reception_form.packaging_state
    #     return result

    type = fields.Selection(selection=[('rc_without_qc', 'RC Without QC'), ('rc_with_qc', 'RC With QC')], string='Type', required=True, default='rc_without_qc')
    all_lot_ids = fields.Many2many('stock.production.lot', 'all_stock_production_lot_reception_form_rel', 'reception_form_id', 'lot_id', string='All Lots')
    available_lot_ids = fields.Many2many('stock.production.lot', 'available_stock_production_lot_reception_form_rel', 'reception_form_id', 'lot_id', string='Available Lots')
    lot_ids = fields.Many2many('stock.production.lot', 'stock_production_lot_reception_form_wizard_rel', 'wizard_id', 'lot_id', string='Lots', domain="[('id', 'in', available_lot_ids)]", required=True)
    picking_id = fields.Many2one('stock.picking', string='Pickings', required=True)

    # validation
    reception_form_ids = fields.Many2many('stock.production.lot.reception.form', 'reception_form_wizard_rel', 'wizard_id', 'form_id', string='Reception Forms')
    hide_edition_fields = fields.Boolean(string='Show Fields', help='Utility field in order to hide edition fields when validating')

    # Reception fields
    packaging_state = fields.Selection([('good', 'Good state'), ('damaged', 'Damaged*')], string='Packaging State')
    form_appendix = fields.Selection([('done', 'Done'), ('not_done', 'Not done*'), ('NA', 'Not applicable')], string='Form Appendix', help='Attach reception and release form as Appendix 1')
    temperature_appendix = fields.Selection([('done', 'Done'), ('not_done', 'Not done*'), ('NA', 'Not applicable')], string='Temperature Appendix', help='Attach shipping temperatures chart as Appendix 2 if temperature-sensitive material')
    materials_conformity = fields.Selection([('yes', 'Yes'), ('no', 'No*'), ('NA', 'Not applicable')], string='Materials Conformity', help='Received materials conform to the specification criteria')
    supplier_consistency = fields.Selection([('consistent', 'Consistent'), ('different', 'Different*')], string='Supplier Consistency', help='Consistency between the delivery note and order to the supplier')
    items_consistency = fields.Selection([('consistent', 'Consistent'), ('different', 'Different*')], string='Items Consistency', help='Consistency of the delivery note with the delivered items')
    reception_comment = fields.Text(string='Explanations', help='Reasons why received materials are not conform and/or appendixes are not done')

    # Status fields
    lot_status = fields.Selection([('released', 'Released for use'), ('rejected', 'Rejected')], string='Status')
    # items_stored = fields.Boolean(string='Items Stored', help='If checked, items should be stored')
    # storage_location = fields.Char(string='Storage Location')

    @api.onchange('form_appendix', 'temperature_appendix', 'materials_conformity')
    def _onchange_reception_comment(self):
        if self.form_appendix != 'not_done' and self.temperature_appendix != 'not_done' and self.materials_conformity != 'no':
            self.reception_comment = ''

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'rc_without_qc':
            self.lot_ids = False
            self.available_lot_ids = self.all_lot_ids.filtered(lambda lot: lot.product_critical_level in ['furniture', 'less_critical', 'intermediary'])
        elif self.type == 'rc_with_qc':
            self.lot_ids = False
            self.available_lot_ids = self.all_lot_ids.filtered(lambda lot: lot.product_critical_level == 'critical')

    # @api.onchange('items_stored')
    # def _onchange_storage_location(self):
    #     if not self.items_stored:
    #         self.storage_location = ''

    def validate_reception_forms(self):
        self.ensure_one()
        for form in self.reception_form_ids:
            form.with_context(form_lot_status=self.lot_status).sign_form()
        return {}

    def create_reception_forms(self):
        self.ensure_one()
        for lot in self.lot_ids:
            vals = {
                'state': 'confirmed',
                'type': self.type,
                'picking_id': self.picking_id.id,
                'lot_id': lot.id,
                'arrival_date': self.picking_id.date_done.date(),
                'specification_reference': lot.product_id.specification_ref,
                'storage_temperature': lot.product_id.storage_temperature,
                'manual_temperature': lot.product_id.manual_temperature,
                'lot_status': self.lot_status,
                # 'items_stored': self.items_stored,
                # 'storage_location': self.storage_location,
                'packaging_state': self.packaging_state,
                'form_appendix': self.form_appendix,
                'temperature_appendix': self.temperature_appendix,
                'materials_conformity': self.materials_conformity,
                'supplier_consistency': self.supplier_consistency,
                'items_consistency': self.items_consistency,
                'reception_comment': self.reception_comment,
                'expiration_date': lot.expiration_date or False,
                'product_qty': lot.product_qty,
                'company_id': lot.company_id.id
            }
            forms = self.env['stock.production.lot.reception.form'].create(vals)
            # chatter notification
            body = _('{} {} been created:\n').format(len(forms), _("form has") if len(forms) <= 1 else _("forms have"))
            for form in forms:
                form_url = f'<a href=# data-oe-model={form._name} data-oe-id={form.id}>{form.name}</a>\n'
                body = body + form_url
            self.picking_id.message_post(body=body)

            if self.env.context.get('send_form'):
                forms.send_form()
        return {}
