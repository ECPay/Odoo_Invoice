{
    'name': 'ECPay 綠界第三方電子發票模組',
    'version': '16.0.1.0',
    'category': 'Accounting',
    'author': 'ECPAY',
    'website': 'http://www.ecpay.com.tw',
    'description': """
        綠界 台灣電子發票Odoo模組\n
        使用 pyhton3\n
        需要依賴模組 ecpay_invoice3\n
        sudo pip3 install ecpay_invoice3
    """,
    'summary': '電子發票 (Invoice): ECPay 綠界第三方電子發票模組',
    'depends': ['account', 'sale', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'security/ecpay_invoice_groups.xml',
        'views/res_config_setting_view.xml',
        'views/account_invoice_view.xml',
        'views/uniform_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/res_company.xml',
        'wizard/invoice_invalid_wizard.xml',
        'wizard/action_invalid_invoice_wizard.xml',
        'views/menu.xml',
        'data/demo.xml',
        'report/uniform_invoice_report.xml'
    ],
    'external_dependencies': {
        'python': ['pycryptodome'],
        'bin': [],
    },
    "assets": {
        "web.assets_frontend": [
            "ecpay_invoice_tw/static/src/css/invoice.css",
        ],
    },
    'installable': True,
    'application': True,
}
