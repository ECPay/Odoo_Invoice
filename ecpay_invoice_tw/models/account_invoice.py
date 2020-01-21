
from odoo import models, fields, api
from ecpay_invoice.ecpay_main import *
from odoo.exceptions import UserError
from werkzeug import urls

import decimal


class ECPAYINVOICEInherit(models.Model):
    _inherit = "account.invoice"

    ecpay_invoice_id = fields.Many2one(comodel_name='uniform.invoice', string='統一發票號碼')
    uniform_state = fields.Selection(selection=[('to invoice', '未開電子發票'), ('invoiced', '已開電子發票'), ('invalid', '已作廢')], string='電子發票狀態',
                                     default='to invoice')
    ecpay_tax_type = fields.Selection(selection=[('1', '含稅'), ('0', '未稅')], string='商品單價是否含稅', default='1',
                                      readonly=True, states={'draft': [('readonly', False)]})
    show_create_invoice = fields.Boolean(string='控制是否顯示串接電子發票', compute='get_access_invoce_mode')
    show_hand_in_field = fields.Boolean(string='控制是否顯示手動填入的選項', compute='get_access_invoce_mode')

    is_donation = fields.Boolean(string='是否捐贈發票')
    lovecode = fields.Char(string='捐贈碼')
    is_print = fields.Boolean(string='是否索取紙本發票')
    carruerType = fields.Selection(selection=[('1', '綠界科技電子發票載具'), ('2', '自然人憑證'), ('3', '手機條碼')], string='載具類別')
    carruernum = fields.Char(string='載具號碼')
    ecpay_CustomerIdentifier = fields.Char(string='統一編號')
    ec_print_address = fields.Char(string='發票寄送地址')
    ec_ident_name = fields.Char(string='發票抬頭')

    IIS__Sales_Amount = fields.Char(string='發票金額', related='ecpay_invoice_id.IIS_Sales_Amount')
    IIS_Invalid_Status = fields.Selection(related='ecpay_invoice_id.IIS_Invalid_Status')
    IIS_Issue_Status = fields.Selection(related='ecpay_invoice_id.IIS_Issue_Status')
    IIS_Relate_Number = fields.Char(related='ecpay_invoice_id.IIS_Relate_Number')

    is_refund = fields.Boolean(string='是否為折讓')
    refund_finish = fields.Boolean(string='折讓完成')
    refund_state = fields.Selection(selection=[('draft', '草稿'),('to be agreed', '待同意'), ('agreed', '開立成功'), ('disagree', '開立失敗')],
                                     string='折讓通知狀態',
                                     default='draft')
    refund_ecpay_kind = fields.Selection([('offline', '紙本同意'), ('online', '線上同意')],
        default='offline', string='同意類型', required=True, help='折讓電子發票同意類型')

    IA_Allow_No = fields.Char(string='折讓單號')
    IA_Invoice_No = fields.Many2one(string='被折讓的發票', related='ecpay_invoice_id')
    IIS_Remain_Allowance_Amt = fields.Char(string='剩餘可折讓金額', related='ecpay_invoice_id.IIS_Remain_Allowance_Amt')

    ecpay_invoice_code = fields.Char(string='綠界電子發票自訂編號 ')

    @api.onchange('is_print', 'carruerType','carruernum')
    def set_carruerType_false(self):
        if self.is_print is True:
            self.is_donation = False
            self.carruerType = False
            self.carruernum = False
        #if self.is_print is True and self.carruerType is not False:
        #    self.carruerType = False
        #    self.carruernum = False

    @api.onchange('is_donation')
    def set_is_print_false(self):
        if self.is_donation is True:
            self.is_print = False

    # 控制是否顯示手動開立的按鈕
    # 注意depends的self有時會有多筆，需要以for loop來執行。
    @api.depends('ecpay_invoice_id')
    def get_access_invoce_mode(self):
        auto_invoice_mode = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.auto_invoice')
        for row in self:
            if auto_invoice_mode == 'automatic':
                row.show_create_invoice = False
            elif auto_invoice_mode == 'hand in':
                row.show_hand_in_field = True
            else:
                row.show_create_invoice = True
                row.show_hand_in_field = False

    # 當開立模式是自動開立時，在發票進行驗證(打開)時，同時進行開立發票的動作。
    @api.multi
    def action_invoice_open(self):
        res = super(ECPAYINVOICEInherit, self).action_invoice_open()
        auto_invoice = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.auto_invoice')
        # 如果發票為折讓，則不自動產生電子發票
        if auto_invoice == 'automatic':
            if self.type in ['out_invoice']:
                self.create_ecpay_invoice()
            elif self.is_refund is True:
                self.run_refund()
        return res

    # 準備基本電子發票商家參數
    def demo_invoice_init(self, ecpay_invoice, type, method):
        # 判斷設定是否為測試電子發票模式
        url = 'https://einvoice.ecpay.com.tw/' + type
        ecpay_demo_mode = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_demo_mode')
        if ecpay_demo_mode:
            url = 'https://einvoice-stage.ecpay.com.tw/' + type

        ecpay_invoice.Invoice_Method = method
        ecpay_invoice.Invoice_Url = url
        ecpay_invoice.MerchantID = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_MerchantID')
        ecpay_invoice.HashKey = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_HashKey')
        ecpay_invoice.HashIV = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_HashIV')

    # 匯入Odoo發票明細到電子發票中
    def prepare_item_list(self):
        res = []
        amount_total = 0.0
        for line in self.invoice_line_ids:
            #若Vat = 0(免稅)，商品金額需為免稅金額若Vat = 1(含稅)，商品金額需為含稅金額
            if self.ecpay_tax_type == '0':
                ItemPrice = line.price_subtotal / int(line.quantity)
                ItemAmount = line.price_subtotal
            else:
                ItemPrice = line.price_total / int(line.quantity)
                ItemAmount = line.price_total

            res.append({
                'ItemName': line.product_id.name[:30],
                'ItemCount': int(line.quantity),
                'ItemWord': line.uom_id.name[:6],
                'ItemPrice': ItemPrice,
                'ItemTaxType': '',
                'ItemAmount': ItemAmount,
                'ItemRemark': line.name[:40]
            })
            #amount_total += line.price_unit * line.quantity
            amount_total += line.price_total
        return res, amount_total

    # 準備客戶基本資料
    def prepare_customer_info(self, ecpay_invoice):

        ecpay_invoice.Send['CustomerID'] = ''
        # 新版統編寫法，取得電商前端統編
        ecpay_invoice.Send['CustomerIdentifier'] = self.ecpay_CustomerIdentifier if self.ecpay_CustomerIdentifier else ''

        # 新版抬頭寫法，取得電商抬頭，如果沒有預設取得partner 名稱
        ecpay_invoice.Send['CustomerName'] = self.ec_ident_name if self.ec_ident_name else self.partner_id.name

        # 新版寄送地址寫法，取得電商發票寄送地址，如果沒有預設取得partner 地址
        ecpay_invoice.Send['CustomerAddr'] = self.ec_print_address if self.ec_print_address else self.partner_id.street
        ecpay_invoice.Send['CustomerPhone'] = self.partner_id.mobile if self.partner_id.mobile else ''
        ecpay_invoice.Send['CustomerEmail'] = self.partner_id.email if self.partner_id.email else ''
        ecpay_invoice.Send['ClearanceMark'] = ''

    # 檢查發票邏輯
    def validate_ecpay_invoice(self):

        if self.is_print is True and self.is_donation is True:
            raise UserError('列印發票與捐贈發票不能同時勾選！！')
        elif self.is_print is True and self.carruerType is not False:
            raise UserError('列印發票時，不能夠選擇發票載具！！')
        elif self.is_print is False and self.carruerType in ['2', '3'] and self.is_donation is False:
            if self.carruernum is False:
                raise UserError('請輸入發票載具號碼！！')
            elif self.carruerType == '3':
                if not self.check_carruernum(self.carruernum):
                    raise UserError('手機載具不存在！！')

        if self.is_donation is True and self.lovecode is not False:
            if not self.check_lovecode(self.lovecode):
                raise UserError('愛心碼不存在！！')

        # 檢查客戶地址
        if self.ec_print_address is False and self.partner_id.street is False:
            raise UserError('請到客戶資料中輸入客戶地址或在當前頁面輸入發票寄送地址！')

    # 產生電子發票
    def create_ecpay_invoice(self):

        # 檢查基本開票邏輯
        self.validate_ecpay_invoice()

        # 建立電子發票物件
        invoice = EcpayInvoice()

        # 設定基本電子發票商家參數
        self.demo_invoice_init(invoice, 'Invoice/Issue', 'INVOICE')

        # 匯入發票種的發票明細到電子發票物件
        invoice.Send['Items'], amount_total = self.prepare_item_list()

        decimal.getcontext().rounding = decimal.ROUND_05UP
        print(round(decimal.Decimal(amount_total)))

        # 匯入客戶基本資訊
        self.prepare_customer_info(invoice)

        # 建立Odoo中，新的uniform.invoice的紀錄
        record = self.env['uniform.invoice'].create({})

        invoice.Send['RelateNumber'] = record.related_number
        invoice.Send['Print'] = '0'
        invoice.Send['Donation'] = '0'
        invoice.Send['LoveCode'] = ''
        invoice.Send['CarruerType'] = ''
        invoice.Send['CarruerNum'] = ''
        invoice.Send['TaxType'] = '1'
        invoice.Send['SalesAmount'] = round(decimal.Decimal(amount_total))
        invoice.Send['InvoiceRemark'] = 'Odoo'
        invoice.Send['InvType'] = '07'
        invoice.Send['vat'] = self.ecpay_tax_type

        # 加入是否捐贈，是否列印，與發票載具的設定
        if self.is_print is True or self.ecpay_CustomerIdentifier:
            invoice.Send['Print'] = '1'
        if self.is_donation is True:
            invoice.Send['Donation'] = '1'
            invoice.Send['LoveCode'] = self.lovecode
        if self.carruerType is not False:
            invoice.Send['CarruerType'] = self.carruerType
            if self.carruernum is not False and invoice.Send['CarruerType'] in ['2', '3']:
                invoice.Send['CarruerNum'] = self.carruernum

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否開立成功
        if aReturn_Info['RtnCode'] != '1':
            raise UserError('串接電子發票失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])

        # 設定發票號碼
        record.name = aReturn_Info['InvoiceNumber']

        # 成功開立發票後，將電子發票與Odoo發票關聯
        self.ecpay_invoice_id = record

        # 利用RelateNumber到綠界後台取得電子發票的詳細資訊並儲存到Odoo電子發票模組
        record.get_ecpay_invoice_info()

        # 設定Odoo發票為已開電子發票
        self.uniform_state = 'invoiced'

    # 執行電子發票作廢
    def run_invoice_invalid(self):
        # 建立物件
        invoice = EcpayInvoice()

        # 初始化物件
        self.demo_invoice_init(invoice, 'Invoice/IssueInvalid', 'INVOICE_VOID')

        # 檢查是否有開立電子發票
        if self.ecpay_invoice_id:
            if self.ecpay_invoice_id.IIS_Invalid_Status == '1':
                raise UserError('該電子發票：%s 已作廢!!' % self.ecpay_invoice_id.name)
        else:
            raise UserError('找不到電子發票!!')

        # 設定電子發票作廢需要參數
        invoice.Send['InvoiceNumber'] = self.ecpay_invoice_id.name
        invoice.Send['Reason'] = self.name

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 判定是否成功作廢
        if aReturn_Info['RtnCode'] != '1':
            raise UserError('作廢電子發票失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])

        # 更新儲存在Odoo中的電子發票資訊
        self.ecpay_invoice_id.get_ecpay_invoice_info()

    # 執行電子發票折讓
    def run_refund(self):
        # 檢查欲折讓的發票是否有被設定
        if self.ecpay_invoice_id.id is False:
            raise UserError('找不到欲折讓的發票！')
        # 取得折讓方式(紙本開立或線上開立)
        #refund_mode = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_AllowanceByCollegiate')
        if self.refund_ecpay_kind=="offline" :
            refund_mode = False
        else :
            refund_mode = True

        # 建立物件
        invoice = EcpayInvoice()
        # 初始化物件,依折讓方式(紙本開立或線上開立)
        if refund_mode :
            if not self.partner_id.email : raise UserError('必需要有客戶e-mail才能通知！')
            self.demo_invoice_init(invoice, 'Invoice/AllowanceByCollegiate', 'AllowanceByCollegiate')
            # 取得 domain
            base_url = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_allowance_domain') if self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_allowance_domain') else self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            invoice.Send['ReturnURL'] = urls.url_join(base_url, '/invoice/ecpay/agreed_invoice_allowance')
        else :
            self.demo_invoice_init(invoice, 'Invoice/Allowance', 'ALLOWANCE')

        invoice.Send['InvoiceNo'] = self.ecpay_invoice_id.name
        invoice.Send['AllowanceNotify'] = 'E'
        invoice.Send['NotifyMail'] = self.partner_id.email if self.partner_id.email else ''

        # 匯入發票種的發票明細到電子發票物件
        invoice.Send['Items'], amount_total = self.prepare_item_list()
        invoice.Send['AllowanceAmount'] = int(self.amount_total)

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否開立成功
        if aReturn_Info['RtnCode'] != '1':
            raise UserError('折讓開立失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])
        # 寫入折讓號碼
        self.IA_Allow_No = aReturn_Info['IA_Allow_No']
        # 更新發票的剩餘折讓金額
        self.ecpay_invoice_id.IA_Remain_Allowance_Amt = aReturn_Info['IA_Remain_Allowance_Amt']
        self.refund_finish = True
        #若為線上開立，還需處理後續狀態
        if refund_mode :
            self.refund_state = 'to be agreed'
        else:
            self.refund_state = 'agreed'

    # 電子發票前端驗證手機條碼ＡＰＩ
    @api.model
    def check_carruernum(self, text):
        # 建立電子發票物件
        invoice = EcpayInvoice()
        # 初始化物件
        self.demo_invoice_init(invoice, 'Query/CheckMobileBarCode', 'CHECK_MOBILE_BARCODE')

        # 準備傳送參數
        invoice.Send['BarCode'] = text

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否成功
        if aReturn_Info['RtnCode'] == '1' and aReturn_Info['IsExist'] == 'Y':
            return True
        else:
            return False

    # 電子發票前端驗證愛心碼ＡＰＩ
    @api.model
    def check_lovecode(self, text):
        # 建立電子發票物件
        invoice = EcpayInvoice()
        # 初始化物件
        self.demo_invoice_init(invoice, 'Query/CheckLoveCode', 'CHECK_LOVE_CODE')

        # 準備傳送參數
        invoice.Send['LoveCode'] = text

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否成功
        if aReturn_Info['RtnCode'] == '1' and aReturn_Info['IsExist'] == 'Y':
            return True
        else:
            return False

    # 產生電子發票
    def get_ecpay_invoice(self):
        if self.ecpay_invoice_code is False :
                raise UserError('請填入綠界電子發票自訂編號 ！！')

        # 建立Odoo中，新的uniform.invoice的紀錄
        record = self.env['uniform.invoice'].create({})

        #invoice.Send['RelateNumber'] = record.related_number
        record.related_number = self.ecpay_invoice_code

        # 設定發票號碼
        #record.name = aReturn_Info['InvoiceNumber']

        # 成功開立發票後，將電子發票與Odoo發票關聯
        self.ecpay_invoice_id = record

        # 利用RelateNumber到綠界後台取得電子發票的詳細資訊並儲存到Odoo電子發票模組
        record.get_ecpay_invoice_info()
        record.name=record.IIS_Number

        # 設定Odoo發票為已開電子發票
        self.uniform_state = 'invoiced'
        return True




