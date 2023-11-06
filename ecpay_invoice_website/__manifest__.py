# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    'name': 'ECPay 綠界第三方電子發票模組-電商網站前台',
    'version': '16.0.1.0',
    'category': 'Accounting',
    'author': 'ECPAY',
    'website': 'http://www.ecpay.com.tw',
    'description': """
        綠界 台灣電子發票Odoo模組\n
        使用 pyhton3\n
    """,
    'summary': '電子發票 (Invoice): ECPay 綠界第三方電子發票模組',
    'depends': ['ecpay_invoice_tw', 'website_sale'],
    'data': [
        'views/website_sale.xml',
    ],
    "assets": {
        "web.assets_frontend": [
            "ecpay_invoice_website/static/src/js/invoice.js",
            "ecpay_invoice_website/static/src/scss/invoice.scss",
            "ecpay_invoice_website/static/src/css/invoice.css",
        ],
    },
    'installable': True,
    'application': True,
}
