# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    # New fields in order to prefill CoA

    # Reception fields
    packaging_state = fields.Selection([('good', 'Good state'), ('damaged', 'Damaged')], string='Packaging State')
    coa_appendix = fields.Selection([('done', 'Done'), ('not_done', 'Not done*'), ('NA', 'Not applicable')], string='CoA Appendix', help='Attach CoA as Appendix 1')
    temperature_appendix = fields.Selection([('done', 'Done'), ('not_done', 'Not done*'), ('NA', 'Not applicable')], string='Temperature Appendix', help='Attach shipping temperatures chart as Appendix 2 if temperature-sensitive material')
    materials_conformity = fields.Selection([('yes', 'Yes'), ('no', 'No*'), ('NA', 'Not applicable')], string='Materials Conformity', help='Received materials conform to the specification criteria')
    supplier_consistency = fields.Selection([('consistent', 'Consistent'), ('different', 'Different')], string='Supplier Consistency', help='Consistency between the delivery note and order to the supplier')
    items_consistency = fields.Selection([('consistent', 'Consistent'), ('different', 'Different')], string='Items Consistency', help='Consistency of the delivery note with the delivered items')
    reception_comment = fields.Text(string='Explanations', help='Reasons why received materials are not conform and/or appendixes are not done')

    # Label fields
    following_template = fields.Boolean(string='Template Followed', help='If checked, prepare labels following the template')
    total_labels = fields.Integer(string='Total Labels', help='Total is equal to n+1')
    specimen_sticked = fields.Boolean(string='Specimen Sticked', help='If checked, specimen should be sticked')

    # Status fields
    lot_status = fields.Selection([('released', 'Released for use'), ('rejected', 'Rejected')], string='Status')
    products_sticked = fields.Boolean(string='Products Sticked', help='If checked, reagents/consumables should be sticked')
    label_reconciliation = fields.Selection([('yes', 'Yes'), ('no', 'No**')], string='Label Reconciliation', help='Exact number on reconciliation')
    items_stored = fields.Boolean(string='Items Stored', help='If checked, items should be stored')
    storage_location = fields.Char(string='Storage Location')
    storage_temperature = fields.Selection([('rt', 'RT'), ('2_8', '2-8°C'), ('80', '-80°C')], string='Storage Temperature')
    manual_temperature = fields.Char(string='Manual Temperature')
    status_comment = fields.Text(string='Comment', help='Comment on label reconciliation')
    table_update = fields.Boolean(string='Table Update', help='OP.1.2_TAB_002 Table for stock management for reagents and consumables')

    # Computed fields
    move_line_ids = fields.One2many('stock.move.line', 'lot_id', string='Operations', readonly=True)
    arrival_date = fields.Date(string='Arrival Date', compute='_compute_arrival_date', store=True, help='Completion date of the last incoming transfer')
    partner_id = fields.Many2one('res.partner', string='Vendor', compute='_compute_arrival_date', store=True, help='Vendor of the purchase order linked to the last incoming transfer')

    @api.depends('move_line_ids.picking_id.date_done')
    def _compute_arrival_date(self):
        for lot in self:
            pickings = lot.move_line_ids.mapped('picking_id').filtered(lambda pick: pick.picking_type_code == 'incoming' and pick.state == 'done' and pick.purchase_id)
            # dates_list = [date for date in pickings.mapped('date_done') if date]
            # lot.arrival_date = max(dates_list).date() if dates_list else False
            arrival_date = False
            partner = False
            if pickings:
                last_pick = pickings.sorted(key=lambda pick: pick.date_done, reverse=True)[0]
                arrival_date = last_pick.date_done.date()
                partner = last_pick.purchase_id.partner_id
            lot.arrival_date = arrival_date
            lot.partner_id = partner.id if partner else False

    @api.onchange('coa_appendix', 'temperature_appendix', 'materials_conformity')
    def _onchange_reception_comment(self):
        if self.coa_appendix != 'not_done' and self.temperature_appendix != 'not_done' and self.materials_conformity != 'no':
            self.reception_comment = ''

    @api.onchange('following_template')
    def _onchange_total_labels(self):
        if not self.following_template:
            self.total_labels = 0

    @api.onchange('products_sticked')
    def _onchange_label_reconciliation(self):
        if not self.products_sticked:
            self.label_reconciliation = False

    @api.onchange('items_stored')
    def _onchange_storage_location(self):
        if not self.items_stored:
            self.storage_location = ''

    @api.onchange('items_stored')
    def _onchange_storage_temperature(self):
        if not self.items_stored:
            self.storage_temperature = False

    @api.onchange('label_reconciliation')
    def _onchange_status_comment(self):
        if self.label_reconciliation != 'no':
            self.status_comment = ''

    @api.onchange('storage_temperature')
    def _onchange_manual_temperature(self):
        if self.storage_temperature != 'rt':
            self.manual_temperature = ''
