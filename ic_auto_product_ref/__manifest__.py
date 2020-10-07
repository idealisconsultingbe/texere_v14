# -*- coding: utf-8 -*-
# Part of Idealis Consulting. See LICENSE file for full copyright and licensing details.

{
    'name': 'Automatic Reference for Product Templates',
    'version': '14.0.0.1',
    'category': 'Sales',
    'summary': """ 
    This module allows to automatically fill the internal reference of a Product with a sequence
    """,
    'author': 'Idealis Consulting',
    'website': 'http://www.idealisconsulting.com',
    'depends': ['product'],
    'data': [
        'data/product_data.xml',
        'views/product_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
