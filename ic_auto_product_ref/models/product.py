# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Idealis Consulting
#    Copyright (c) 2016 Idealis Consulting S.A. (http://www.idealisconsulting.com)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, values):
        """
        Override create to set default code if not present in values
        :param values: record values
        :return: inherited create function value
        """
        if 'default_code' not in values:
            values['default_code'] = self.env['ir.sequence'].next_by_code('ic.product.default.code.sequence')
        return super(ProductTemplate, self).create(values)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, values):
        """
        Override create to set default code if not present in values
        :param values: record values
        :return: inherited create function value
        """
        if 'default_code' not in values:
            values['default_code'] = self.env['ir.sequence'].next_by_code('ic.product.default.code.sequence')
        return super(ProductProduct, self).create(values)
