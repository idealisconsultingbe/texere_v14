# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

{
    'name': 'Reception and Release Management',
    'version': '14.0.0.2',
    'category': 'Manufacturing/Quality',
    'description': """ 
    This module allows users to create the product reception and release form with prefilled values
    """,
    'author': 'Idealis Consulting',
    'website': 'http://www.idealisconsulting.com',
    'depends': ['web', 'purchase_stock', 'hr', 'sign', 'quality_control'],
    'data': [
        'data/reception_form_data.xml',
        'security/ir.model.access.csv',
        'views/quality_point_views.xml',
        'views/stock_picking_views.xml',
        'views/product_template_views.xml',
        'views/stock_production_lot_reception_form_views.xml',
        'views/stock_production_lot_views.xml',
        'views/reception_and_release_templates.xml',
        'report/reception_and_release_templates.xml',
        'report/reception_and_release_report.xml',
        'wizard/create_reception_form_views.xml',
        'views/product_category_views.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
