# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

{
    'name': 'CoA Management',
    'version': '14.0.0.1',
    'category': 'Manufacturing/Quality',
    'description': """ 
    This module allows users to create the product CoA with prefilled values
    """,
    'author': 'Idealis Consulting',
    'website': 'http://www.idealisconsulting.com',
    'depends': ['stock', 'web', 'purchase_stock'],
    'data': [
        'views/stock_production_lot_views.xml',
        'views/coa_templates.xml',
        'report/coa_templates.xml',
        'report/coa_report.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
