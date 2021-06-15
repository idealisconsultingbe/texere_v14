# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class CustomWarning(models.TransientModel):
    _name = 'reception.form.custom.warning'
    _description = 'Release and Reception Form Custom Warning'

    title = fields.Char(string='Title', required=True)
    description = fields.Text(string='Description', required=True)
