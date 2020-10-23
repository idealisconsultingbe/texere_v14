# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.
import base64
from odoo import api, fields, models, _
from werkzeug.urls import url_encode


class LotReceptionForm(models.Model):
    _name = 'stock.production.lot.reception.form'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Ref', index=True, required=True, states={'validated': [('readonly', True)]})
    picking_id = fields.Many2one('stock.picking', string='Incoming Transfer', required=True, readonly=True, states={'draft': [('readonly', False)]})
    lot_id = fields.Many2one('stock.production.lot', string='Lot', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, index=True, default=lambda self: self.env.company)

    product_id = fields.Many2one('product.product', string='Product', related='lot_id.product_id', store=True)
    purchase_id = fields.Many2one('purchase.order', string='Order', related='picking_id.purchase_id', store=True)
    partner_id = fields.Many2one('res.partner', string='Vendor', related='purchase_id.partner_id', store=True)
    product_uom_id = fields.Many2one('uom.uom', string='Product UoM', related='lot_id.product_uom_id', store=True)
    product_categ_id = fields.Many2one('product.category', string='Product Category', related='lot_id.product_id.categ_id', store=True)
    seller_product_code = fields.Char(string='Seller Product Code', compute='_compute_seller_product_code', store=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'), ('sent', 'Sent'), ('validated', 'Validated')], tracking=True, index=True, readonly=True, string='Status', default='draft')

    # Reception fields
    packaging_state = fields.Selection([('good', 'Good state'), ('damaged', 'Damaged')], string='Packaging State', states={'validated': [('readonly', True)]})
    form_appendix = fields.Selection([('done', 'Done'), ('not_done', 'Not done*'), ('NA', 'Not applicable')], string='Form Appendix', help='Attach reception and release form as Appendix 1', states={'validated': [('readonly', True)]})
    temperature_appendix = fields.Selection([('done', 'Done'), ('not_done', 'Not done*'), ('NA', 'Not applicable')], string='Temperature Appendix', help='Attach shipping temperatures chart as Appendix 2 if temperature-sensitive material', states={'validated': [('readonly', True)]})
    materials_conformity = fields.Selection([('yes', 'Yes'), ('no', 'No*'), ('NA', 'Not applicable')], string='Materials Conformity', help='Received materials conform to the specification criteria', states={'validated': [('readonly', True)]})
    supplier_consistency = fields.Selection([('consistent', 'Consistent'), ('different', 'Different'), ('NA', 'Not applicable')], string='Supplier Consistency', help='Consistency between the delivery note and order to the supplier', states={'validated': [('readonly', True)]})
    items_consistency = fields.Selection([('consistent', 'Consistent'), ('different', 'Different'), ('NA', 'Not applicable')], string='Items Consistency', help='Consistency of the delivery note with the delivered items', states={'validated': [('readonly', True)]})
    reception_comment = fields.Text(string='Explanations', help='Reasons why received materials are not conform and/or appendixes are not done', states={'validated': [('readonly', True)]})

    arrival_date = fields.Date(string='Arrival Date', states={'validated': [('readonly', True)]})
    specification_reference = fields.Char(string='Reference', states={'validated': [('readonly', True)]})
    expiration_date = fields.Date(string='Expiry Date', states={'validated': [('readonly', True)]})
    product_qty = fields.Float(string='Quantity', states={'validated': [('readonly', True)]})

    # Status fields
    lot_status = fields.Selection([('released', 'Released for use'), ('rejected', 'Rejected')], string='Status', states={'validated': [('readonly', True)]})
    items_stored = fields.Boolean(string='Items Stored', help='If checked, items should be stored', states={'validated': [('readonly', True)]})
    storage_location = fields.Char(string='Storage Location', states={'validated': [('readonly', True)]})
    storage_temperature = fields.Selection([('rt', 'RT'), ('2_8', '2-8°C'), ('80', '-80°C')], string='Storage Temperature', states={'validated': [('readonly', True)]})
    manual_temperature = fields.Char(string='Manual Temperature', states={'validated': [('readonly', True)]})

    # reception signature
    receipt_signature = fields.Binary(string='Receipt Signature', readonly=True, help='Signature made by reception team', copy=False)
    receipt_signed_by = fields.Many2one('res.users', string='Receipt Signed By', readonly=True, help='Name of the person that received the lot', copy=False)
    receipt_signed_on = fields.Datetime(string='Receipt Signed On', readonly=True, help='Date of the signature', copy=False)

    # status signature
    signature = fields.Binary(string='Signature', readonly=True, help='Signature made by quality team', copy=False)
    signed_by = fields.Many2one('res.users', string='Signed By', readonly=True, help='Name of the person that signed the R&R form', copy=False)
    signed_on = fields.Datetime(string='Signed On', readonly=True, help='Date of the signature', copy=False)
    job_title = fields.Char(string='Job Position', related='signed_by.job_title', store=True, copy=False)

    @api.depends('product_id.seller_ids.name', 'product_id.seller_ids.product_code')
    def _compute_seller_product_code(self):
        for form in self:
            form.seller_product_code = ''
            if form.partner_id in form.product_id.seller_ids.mapped('name'):
                supplierinfo = form.product_id.seller_ids.filtered(
                    lambda supplierinfo: supplierinfo.name == form.partner_id and supplierinfo.product_code)
                form.seller_product_code = supplierinfo[0].product_code if supplierinfo else ''

    @api.onchange('form_appendix', 'temperature_appendix', 'materials_conformity')
    def _onchange_reception_comment(self):
        if self.form_appendix != 'not_done' and self.temperature_appendix != 'not_done' and self.materials_conformity != 'no':
            self.reception_comment = ''

    @api.onchange('items_stored')
    def _onchange_storage_location(self):
        if not self.items_stored:
            self.storage_location = ''

    @api.onchange('items_stored')
    def _onchange_storage_temperature(self):
        if not self.items_stored:
            self.storage_temperature = False

    @api.onchange('storage_temperature')
    def _onchange_manual_temperature(self):
        if self.storage_temperature != 'rt':
            self.manual_temperature = ''

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stock.production.lot.reception.form') or _('New')
        return super(LotReceptionForm, self).create(vals)

    def action_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirmed'})

    def sign_form(self):
        self.ensure_one()
        self.write({
            'signed_by': self.env.user.id,
            'signed_on': fields.Datetime.now(),
            'signature': self.env.user.sign_signature,
            'state': 'validated',
        })
        pdf = self.env.ref('reception_and_release_management.action_report_reception_and_release_form')._render(self.id)
        b64_pdf = base64.b64encode(pdf[0])
        attachment = self.env['ir.attachment'].create({
            'name': '[{}]Reception_and_release_form-lot{}.pdf'.format(self.state.upper(), (self.lot_id.name).replace('/', '')),
            'type': 'binary',
            'datas': b64_pdf,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })
        body = _('Form signed by {} on {}').format(self.signed_by.name, self.signed_on)
        self.message_post(body=body, attachment_ids=[attachment.id])

    def send_form(self):
        self.ensure_one()
        # change record state
        self.write({
            'receipt_signed_by': self.env.user.id,
            'receipt_signed_on': fields.Datetime.now(),
            'receipt_signature': self.env.user.sign_signature,
            'state': 'sent' if self.env.context.get('send_form') else 'confirmed'
        })

        if self.env.context.get('send_form'):
            # attach pdf to current record
            # When rendering qweb, record attachment is automatically done if attachment is set on report action

            # pdf = self.env.ref('reception_and_release_management.action_report_reception_and_release_form').render_qweb_pdf(self.id)
            pdf = self.env.ref('reception_and_release_management.action_report_reception_and_release_form')._render(self.id)
            b64_pdf = base64.b64encode(pdf[0])
            attachment = self.env['ir.attachment'].create({
                'name': '[{}]Reception_and_release_form-lot{}.pdf'.format(self.state.upper(), (self.lot_id.name).replace('/', '')),
                'type': 'binary',
                'datas': b64_pdf,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/x-pdf'
            })
            # have a copy of pdf in chatter
            body = _('Form generated by {} on {}').format(self.receipt_signed_by.name, self.receipt_signed_on)
            self.message_post(body=body, attachment_ids=[attachment.id])

            # notify control point followers
            url = '/web#{}'.format(url_encode({
                'action': self.env.ref('stock.action_production_lot_form').id,
                'id': self.lot_id.id,
                'active_model': 'stock.production.lot',
                'menu_id': self.env.ref('stock.menu_stock_root').id,
                'view_type': 'form'
            }))
            body = _('Reception and release form of lot <a href="{}">{}</a> is waiting for a validation').format(url, self.lot_id.name)
            # TODO= FIX THIS ! control point not reachable due to routes
            control_points = self.picking_id.mapped('check_ids.point_id')
            for point in control_points:
                point.message_post(
                    subject=_('R&R form to Validate'),
                    body=body,
                    subtype='mail.mt_comment',
                    email_layout_xmlid='mail.mail_notification_light',
                )
