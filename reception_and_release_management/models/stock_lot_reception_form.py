# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
import base64
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LotReceptionForm(models.Model):
    _name = 'stock.production.lot.reception.form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Release and Reception Form'

    name = fields.Char(string='Ref', index=True, required=True, states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    picking_id = fields.Many2one('stock.picking', string='Incoming Transfer', required=True, readonly=True, states={'draft': [('readonly', False)]})
    lot_id = fields.Many2one('stock.production.lot', string='Lot', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True, default=lambda self: self.env.company)

    product_id = fields.Many2one('product.product', string='Product', related='lot_id.product_id', store=True)
    purchase_id = fields.Many2one('purchase.order', string='Order', related='picking_id.purchase_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Supplier', related='purchase_id.partner_id', store=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='lot_id.product_uom_id', store=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='lot_id.product_id.categ_id', store=True)
    seller_product_code = fields.Char(string='Supplier Product Code', compute='_compute_seller_product_code', store=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ('sent', 'Sent'), ('approved', 'Approved'), ('closed', 'Closed')], tracking=True, index=True, readonly=True, string='Status', default='draft')
    type = fields.Selection(selection=[('rc_without_qc', 'RC Without QC'), ('rc_with_qc', 'RC With QC'), ('qc_result', 'QC Results')], default='rc_without_qc', tracking=True, index=True, readonly=True, string='Type')

    # RR parent
    child_ids = fields.One2many('stock.production.lot.reception.form', 'parent_id', string='R&R Children', tracking=True, readonly=True)
    closed_by = fields.Many2one('res.users', string='Closed By', readonly=True, help='Name of the person that closed the parent R&R form')
    closed_on = fields.Datetime(string='Closed On', readonly=True, help='Closure Date')
    total_qty_tested = fields.Float(string='Total Quantities Tested', states={'closed': [('readonly', True)]})
    reconciliation_consistency = fields.Selection([('consistent', 'Consistent'), ('not_consistent', 'Not consistent')], string='Reconciliation Consistency', help='Consistency of the tested quantities according to form quantities', states={'closed': [('readonly', True)]})
    reconciliation_comment = fields.Text(string='Reconciliation Comment', help='Reasons why tested quantities are not consistent with quantities set on R&R form', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})

    # RR child
    parent_id = fields.Many2one('stock.production.lot.reception.form', string='R&R Parent', tracking=True, readonly=True)

    # Reception fields
    packaging_state = fields.Selection([('good', 'Good state'), ('damaged', 'Damaged')], string='Packaging State', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    form_appendix = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('NA', 'Not applicable')], string='CoA Appendix', help='Attach certificate of analysis as Appendix 1', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    temperature_appendix = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('NA', 'Not applicable')], string='Temperature Appendix', help='Attach shipping temperatures chart as Appendix 2 if temperature-sensitive material', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})

    materials_conformity = fields.Selection([('criteria_met', 'Criteria met'), ('criteria_not_met', 'Criteria not met'), ('NA', 'Not applicable')], string='Materials Conformity', help='Received materials conform to the specification criteria', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    ordered_consistency = fields.Selection([('consistent', 'Consistent'), ('not_consitent', 'Not consistent')], string='Ordered Consistency', help='Consistency between the delivery note and order to the supplier', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    received_consistency = fields.Selection([('consistent', 'Consistent'), ('not_consistent', 'Not consistent')], string='Delivered Consistency', help='Consistency of the delivery note with the delivered items', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    reception_comment = fields.Text(string='Explanations', help='Reasons why received materials are not conform and/or critera are not met', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})

    arrival_date = fields.Date(string='Arrival Date', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    specification_reference = fields.Char(string='Reference', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    expiration_date = fields.Date(string='Expiry Date', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    product_qty = fields.Float(string='Quantity', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})

    # Status fields
    lot_status = fields.Selection([('released', 'Released for use'), ('rejected', 'Rejected')], string='Lot Status', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    items_stored = fields.Boolean(string='Items Stored', help='If checked, items should be stored', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    storage_location = fields.Char(string='Storage Location', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})
    storage_temperature = fields.Selection([('rt', '+15/+25°C (RT)'), ('2_8', '+2/+8°C'), ('80', '-80°C')], string='Storage Temperature', states={'approved': [('readonly', True)], 'closed': [('readonly', True)]})

    # reception signature
    receipt_signed_by = fields.Many2one('res.users', string='Receipt Signed By', readonly=True, help='Name of the person that received the lot')
    receipt_signed_on = fields.Datetime(string='Receipt Signed On', readonly=True, help='Date of the signature')

    # status signature
    signed_by = fields.Many2one('res.users', string='Signed By', readonly=True, help='Name of the person that signed the R&R form')
    signed_on = fields.Datetime(string='Signed On', readonly=True, help='Signature Date')

    @api.depends('product_id.seller_ids.name', 'product_id.seller_ids.product_code')
    def _compute_seller_product_code(self):
        for form in self:
            form.seller_product_code = ''
            if form.partner_id in form.product_id.seller_ids.mapped('name'):
                supplierinfo = form.product_id.seller_ids.filtered(
                    lambda supplierinfo: supplierinfo.name == form.partner_id and supplierinfo.product_code)
                form.seller_product_code = supplierinfo[0].product_code if supplierinfo else ''

    @api.onchange('ordered_consistency', 'received_consistency', 'materials_conformity')
    def _onchange_reception_comment(self):
        if self.materials_conformity != 'criteria_not_met' and self.received_consistency != 'not_consistent' and self.ordered_consistency != 'not_consistent':
            self.reception_comment = ''

    @api.onchange('items_stored')
    def _onchange_items_stored(self):
        if not self.items_stored:
            self.storage_location = ''

    @api.constrains('state', 'type')
    def _check_state(self):
        for record in self:
            if record.state == 'closed' and record.type != 'rc_with_qc':
                raise UserError(_('Only RC with QC can be closed ({}).').format(record.name))

    @api.constrains('produt_id', 'type')
    def _check_type(self):
        for record in self:
            if record.product_id and record.product_id.categ_id.critical_level == 'critical' and record.type not in ['qc_result', 'rc_with_qc']:
                raise UserError(
                    _('Critical products should only trigger a RC with QC or QC results ({}).').format(record.name))
            if record.product_id and record.product_id.categ_id.critical_level in ['intermediary', 'less_critical', 'furniture'] and record.type != 'rc_without_qc':
                raise UserError(
                    _('Non-critical products should only trigger a RC without QC ({}).').format(record.name))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stock.production.lot.reception.form') or _('New')
        res = super().create(vals)
        reception_form_actions = self.env['reception.form.action'].search([('action', '=', 'notify'),
                                                                           ('form_type', '=', res.type),
                                                                           ('form_state', '=', res.state),
                                                                           ('company_id', '=', res.company_id.id)])
        if reception_form_actions:
            res.with_context(new_record=True)._notify(reception_form_actions)
        return res

    def write(self, values):
        res = super().write(values)
        reception_form_actions = self.env['reception.form.action'].search([('action', '=', 'notify'),
                                                                           ('form_type', '=', self.type),
                                                                           ('form_state', '=', self.state),
                                                                           ('company_id', '=', self.company_id.id)])
        if reception_form_actions:
            self._notify(reception_form_actions)
        return res

    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})

    def sign_form(self):
        self.ensure_one()
        self.write({
            'signed_by': self.env.user.id,
            'signed_on': fields.Datetime.now(),
            'lot_status': self.env.context.get('form_lot_status', 'released'),
            'state': 'approved',
        })
        self._post_message(_('Form signed by {} on {}').format(self.signed_by.name, self.signed_on))

    def send_form(self):

        def get_pickings(pick):
            pickings = pick
            move_lines = pick.move_lines
            for move in move_lines:
                dest_move_lines = move.move_dest_ids
                for dest_move_line in dest_move_lines:
                    pickings |= get_pickings(dest_move_line.picking_id)
            return pickings

        self.ensure_one()
        # change record state
        self.write({
            'receipt_signed_by': self.env.user.id,
            'receipt_signed_on': fields.Datetime.now(),
            'state': 'sent' if self.env.context.get('send_form') else 'confirmed'
        })

        if self.env.context.get('send_form'):
            self._post_message( _('Form generated by {} on {}').format(self.receipt_signed_by.name, self.receipt_signed_on))

            # notify control point followers
            lot_url = '/web#{}'.format(url_encode({
                'action': self.env.ref('stock.action_production_lot_form').id,
                'id': self.lot_id.id,
                'active_model': 'stock.production.lot',
                'menu_id': self.env.ref('stock.menu_stock_root').id,
                'view_type': 'form'
            }))
            form_url = '/web#{}'.format(url_encode({
                'action': self.env.ref('reception_and_release_management.action_reception_form').id,
                'id': self.id,
                'active_model': 'stock.production.lot.reception.form',
                'menu_id': self.env.ref('reception_and_release_management.reception_and_release_form_menu').id,
                'view_type': 'form'
            }))
            body = _('Reception and release form <a href="{}">{}</a> of lot <a href="{}">{}</a> is waiting for a validation')\
                .format(form_url, self.name, lot_url, self.lot_id.name)
            pickings = get_pickings(self.picking_id)
            checks = self.env['quality.check'].search([('picking_id', 'in', pickings.ids), ('quality_state', '=', 'none')])
            for check in checks:
                check.message_post(
                    subject=_('R&R form to Validate'),
                    body=body,
                    message_type='comment',
                    subtype_xmlid='mail.mt_note'
                )
            for point in checks.mapped('point_id'):
                point.message_post(
                    subject=_('R&R form to Validate'),
                    body=body,
                    subtype_xmlid='mail.mt_comment',
                    email_layout_xmlid='mail.mail_notification_light',
                )

    def _notify(self, reception_form_actions):
        partners = reception_form_actions.mapped('group_id.users.partner_id')
        subject = _('Release and Reception Form {} {}').format(self.name, self.state)
        body = self.env['ir.qweb']._render('reception_and_release_management.reception_form_body_message', {
            'state': self.state,
            'new_record': self._context.get('new_record', False),
            'res_model': self._name,
            'res_id': self.id,
            'res_name': self.name,
            'model_description': self._description,
            'access_link': self.env['mail.thread']._notify_get_action_link('view', model=self._name, res_id=self.id),
        })
        odoobot = self.env.ref('base.partner_root')

        self.env['mail.thread'].sudo().message_notify(
            subject=subject,
            body=body,
            author_id=odoobot.id,
            partner_ids=partners.ids,
            email_layout_xmlid='mail.mail_notification_light',
            model_description=self._description,
        )

    def _post_message(self, body):
        # attach pdf to current record
        # When rendering qweb, record attachment is automatically done if attachment is set on report action
        pdf = self.env.ref('reception_and_release_management.action_report_reception_and_release_form')._render(self.id)
        b64_pdf = base64.b64encode(pdf[0])
        attachment = self.env['ir.attachment'].create({
            'name': '[{}]Reception_and_release_form-lot{}.pdf'.format(self.state.upper(), self.lot_id.name.replace('/', '')),
            'type': 'binary',
            'datas': b64_pdf,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        # have a copy of pdf in chatter
        self.message_post(body=body, attachment_ids=[attachment.id])
