{
    'name': 'ECPay 綠界第三方電子發票模組',
    'version': '1.4',
    'category': 'Accounting',
    'author': 'Chang Chia-Ming',
    'website': 'http://blog.alltop.com.tw/alltopco/',
    'description': """
        綠界 台灣電子發票Odoo模組\n
        使用 pyhton3\n
        需要依賴模組 ecpay_invoice3\n
        sudo pip3 install ecpay_invoice3
    """,
    'summary': '電子發票 (Invoice): ECPay 綠界第三方電子發票模組',
    'depends': ['account', 'sale', 'website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_setting_view.xml',
        'views/account_invoice_view.xml',
        'views/uniform_invoice_view.xml',
        'views/website_sale.xml',
        'views/sale_order_view.xml',
        'views/menu.xml',
        'data/demo.xml',
        'report/uniform_invoice_report.xml'
    ],
    'external_dependencies': {
        'python': [
            'ecpay_invoice'
        ],
        'bin': []
    },
    'installable': True,
    'application': True,
}
