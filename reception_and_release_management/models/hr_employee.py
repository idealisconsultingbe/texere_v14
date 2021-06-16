# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Employee(models.Model):
    _inherit = 'hr.employee'

    trigram = fields.Char(string='Trigram', size=3, tracking=True, groups='hr.group_hr_user')

    @api.constrains('trigram')
    def _check_trigram(self):
        for employee in self:
            if employee.trigram and len(employee.trigram) < 2:
                raise ValidationError(_("Employee's trigram should be 3 letters long (employee: {}, trigram: {}).").format(employee.name, employee.trigram))
