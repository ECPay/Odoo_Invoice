# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.ecpay_invoice_tw.sdk.ecpay_main import *
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    ecpay_invoice_id = fields.Many2one('uniform.invoice', string='統一發票號碼', readonly=True, copy=False)

    uniform_state = fields.Selection(
        selection=[('to invoice', '未開電子發票'), ('invoiced', '已開電子發票'), ('invalid', '已作廢'), ('Discounted', '已折讓')],
        string='電子發票狀態',
        default='to invoice', readonly=True, copy=False)
    ecpay_tax_type = fields.Selection(selection=[('1', '含稅'), ('0', '未稅')], string='商品單價是否含稅', default='1',
                                      readonly=True, states={'draft': [('readonly', False)]})

    show_create_invoice = fields.Boolean(string='控制是否顯示串接電子發票', compute='get_access_invoce_mode')
    show_hand_in_field = fields.Boolean(string='控制是否顯示手動填入的選項', compute='get_access_invoce_mode')

    is_donation = fields.Boolean(string='是否捐贈發票', readonly=True, copy=False)
    is_print = fields.Boolean(string='是否索取紙本發票', readonly=True, copy=False)

    carrierType = fields.Selection(selection=[('1', '綠界科技電子發票載具'), ('2', '自然人憑證'), ('3', '手機條碼')],
                                   string='載具類別')

    lovecode = fields.Char(string='捐贈碼', readonly=True, copy=False)
    carrierNum = fields.Char(string='載具號碼', related='ecpay_invoice_id.IIS_Carrier_Num', readonly=True, copy=False)
    ecpay_CustomerIdentifier = fields.Char(string='統一編號', readonly=True, copy=False)
    ec_print_address = fields.Char(string='發票寄送地址', readonly=True, copy=False)
    ec_ident_name = fields.Char(string='發票抬頭', readonly=True, copy=False)

    is_refund = fields.Boolean(string='是否為折讓', readonly=True)
    refund_finish = fields.Boolean(string='折讓完成', readonly=True)

    IA_Allow_No = fields.Char(string='折讓單號', readonly=True, copy=False)
    IA_Invoice_No = fields.Many2one('uniform.invoice', string='要折讓的發票', readonly=True, copy=False)

    III_Invoice_No = fields.Many2one('uniform.invoice', string='要作廢的發票', readonly=True, copy=False)

    IIS_Remain_Allowance_Amt = fields.Char(string='剩餘可折讓金額', related='ecpay_invoice_id.IIS_Remain_Allowance_Amt', copy=False)
    IIS_Sales_Amount = fields.Char(string='發票金額', related='ecpay_invoice_id.IIS_Sales_Amount', copy=False)
    IIS_Invalid_Status = fields.Selection(related='ecpay_invoice_id.IIS_Invalid_Status', copy=False)
    IIS_Issue_Status = fields.Selection(related='ecpay_invoice_id.IIS_Issue_Status', copy=False)
    IIS_Relate_Number = fields.Char(related='ecpay_invoice_id.IIS_Relate_Number', copy=False)

    @api.onchange('is_print', 'carrierType')
    def set_carrierType_false(self):
        if self.is_print is True and self.carrierType is not False:
            self.carrierType = False
            self.carrierNum = False

    @api.onchange('is_donation')
    def set_is_print_false(self):
        if self.is_donation is True:
            self.is_print = False

    # 控制是否顯示手動開立的按鈕
    @api.depends('ecpay_invoice_id', 'IA_Invoice_No', 'III_Invoice_No')
    def get_access_invoce_mode(self):
        for row in self:
            auto_invoice_mode = row.company_id.auto_invoice
            if auto_invoice_mode == 'automatic':
                row.show_create_invoice = False
            elif auto_invoice_mode == 'hand in':
                row.show_create_invoice = False
                row.show_hand_in_field = True
            else:
                row.show_create_invoice = True
                row.show_hand_in_field = False

    # 當開立模式是自動開立時，在應收憑單進行過帳時，同時進行開立發票的動作。
    def action_post(self):
        res = super(AccountMove, self).action_post()
        for row in self.filtered(lambda x: x.uniform_state != 'invoiced' or not x.ecpay_invoice_id):
            auto_invoice = row.company_id.auto_invoice
            # 如果為折讓單，則不自動產生電子發票
            if auto_invoice == 'automatic' and row.move_type == 'out_invoice':
                row.create_ecpay_invoice()
            if auto_invoice == 'automatic' and row.move_type == 'out_refund':
                row.run_refund()

        return res

    # 準備基本電子發票商家參數
    @api.model
    def ecpay_invoice_init(self, ecpay_invoice, api_uri, method, company_id=False):

        company_id = company_id or self.env.company

        # 判斷設定是否為測試電子發票模式
        ecpay_demo_mode = company_id.ecpay_demo_mode
        if ecpay_demo_mode:
            url = 'https://einvoice-stage.ecpay.com.tw/' + api_uri
        else:
            url = 'https://einvoice.ecpay.com.tw/' + api_uri

        ecpay_invoice.Invoice_Method = method
        ecpay_invoice.Invoice_Url = url
        # TODO 檢查以下三個參數，缺少任一個就跳出警告
        if not company_id.ecpay_MerchantID or \
                not company_id.ecpay_HashKey or not company_id.ecpay_HashIV:
            raise UserError('綠界電子發票連線設定不完整')

        ecpay_invoice.MerchantID = company_id.ecpay_MerchantID
        ecpay_invoice.HashKey = company_id.ecpay_HashKey
        ecpay_invoice.HashIV = company_id.ecpay_HashIV

    # 匯入Odoo發票明細到電子發票中
    def prepare_item_list(self):
        self.ensure_one()

        res = []
        amount_total = 0.0
        for line in self.invoice_line_ids:
            taxable = line.tax_ids.filtered(lambda t: t.amount >= 5.0)
            ItemPrice = float_round(line.price_total / int(line.quantity), precision_digits=2)
            res.append({
                'ItemName': line.product_id.name[:30],
                'ItemCount': int(line.quantity),
                'ItemWord': line.product_uom_id.name[:6],
                'ItemPrice': ItemPrice,
                'ItemTaxType': '1' if len(taxable.ids) >= 1 else '3',
                'ItemAmount': float_round(ItemPrice * int(line.quantity), precision_digits=2),
                'ItemRemark': line.name[:40]
            })
            amount_total += line.price_total
        return res, amount_total

    # 準備客戶基本資料
    @api.model
    def prepare_customer_info(self, ecpay_invoice):
        ecpay_invoice.Send['CustomerID'] = ''
        # 新版統編寫法，取得電商前端統編
        ecpay_invoice.Send[
            'CustomerIdentifier'] = self.ecpay_CustomerIdentifier if self.ecpay_CustomerIdentifier else ''

        # 新版抬頭寫法，取得電商抬頭，如果沒有預設取得partner 名稱
        ecpay_invoice.Send['CustomerName'] = self.ec_ident_name if self.ec_ident_name else self.partner_id.name

        # 新版寄送地址寫法，取得電商發票寄送地址，如果沒有預設取得partner 地址
        ecpay_invoice.Send[
            'CustomerAddr'] = self.ec_print_address if self.ec_print_address else self.partner_id.contact_address
        ecpay_invoice.Send['CustomerPhone'] = self.partner_id.mobile if self.partner_id.mobile else ''
        ecpay_invoice.Send['CustomerEmail'] = self.partner_id.email if self.partner_id.email else ''
        ecpay_invoice.Send['ClearanceMark'] = ''

    # 檢查發票邏輯
    def validate_ecpay_invoice(self):
        self.ensure_one()

        if self.move_type != 'out_invoice':
            raise UserError('檢查發票邏輯的應收憑單類型應該為客戶應收憑單')

        if self.is_print is True and self.is_donation is True:
            raise UserError('列印發票與捐贈發票不能同時勾選！！')
        elif self.is_print is True and self.carrierType is not False:
            raise UserError('列印發票時，不能夠選擇發票載具！！')
        elif self.is_print is False and self.carrierType in ['2', '3'] and self.is_donation is False:
            if self.carrierNum is False:
                raise UserError('請輸入發票載具號碼！！')
            elif self.carrierType == '3':
                if not self.check_carrier_num(self.carrierNum):
                    raise UserError('手機載具不存在！！')

        if self.is_donation is True and self.lovecode is not False:
            if not self.check_lovecode(self.lovecode):
                raise UserError('愛心碼不存在！！')

        # 檢查客戶地址
        if self.ec_print_address is False and self.partner_id.street is False:
            raise UserError('請到客戶資料中輸入客戶地址或在當前頁面輸入發票寄送地址！')

    # 產生電子發票
    def create_ecpay_invoice(self):
        self.ensure_one()

        if self.move_type != 'out_invoice':
            raise UserError('產生電子發票的應收憑單類型應該為客戶應收憑單')

        # 檢查基本開票邏輯
        self.validate_ecpay_invoice()

        # 建立電子發票物件
        invoice = EcpayInvoice()

        company_id = self.company_id

        # 設定基本電子發票商家參數
        self.ecpay_invoice_init(invoice, 'B2CInvoice/Issue', 'INVOICE', company_id)

        # 匯入發票種的發票明細到電子發票物件
        invoice.Send['Items'], amount_total = self.prepare_item_list()

        # 匯入客戶基本資訊
        self.prepare_customer_info(invoice)

        # 建立Odoo中，新的uniform.invoice的紀錄
        record = self.env['uniform.invoice'].create({
            'company_id': self.company_id.id
        })

        invoice.Send['RelateNumber'] = record.related_number
        invoice.Send['Print'] = '0'
        invoice.Send['Donation'] = '0'
        invoice.Send['LoveCode'] = ''
        invoice.Send['CarrierType'] = ''
        invoice.Send['carrierNum'] = ''
        invoice.Send['SalesAmount'] = int(float_round(amount_total, precision_digits=0))
        invoice.Send['InvoiceRemark'] = self.name + ('|' + self.invoice_origin if self.invoice_origin else '')
        invoice.Send['InvType'] = '07'
        invoice.Send['vat'] = self.ecpay_tax_type

        TaxTypes = []
        for item in invoice.Send['Items']:
            TaxTypes.append(item['ItemTaxType'])
        TaxType = TaxTypes.pop()
        for item in TaxTypes:
            if TaxType != item:
                TaxType = '9'
                break

        invoice.Send['TaxType'] = TaxType

        # 加入是否捐贈，是否列印，與發票載具的設定
        if self.is_print or self.ecpay_CustomerIdentifier:
            invoice.Send['Print'] = '1'
        if self.is_donation is True:
            invoice.Send['Donation'] = '1'
            invoice.Send['LoveCode'] = self.lovecode
        if self.carrierType is not False:
            invoice.Send['CarrierType'] = self.carrierType
            if self.carrierNum is not False and invoice.Send['CarrierType'] in ['2', '3']:
                invoice.Send['carrierNum'] = self.carrierNum

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否開立成功
        if aReturn_Info['RtnCode'] != 1:
            raise UserError('串接電子發票失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])

        # 設定發票號碼
        record.name = aReturn_Info['InvoiceNo']

        # 成功開立發票後，將電子發票與Odoo發票關聯
        self.ecpay_invoice_id = record

        # 利用RelateNumber到綠界後台取得電子發票的詳細資訊並儲存到Odoo電子發票模組
        record.get_ecpay_invoice_info()

        # 設定Odoo發票為已開電子發票
        self.uniform_state = 'invoiced'

    def action_run_invoice_invalid(self):
        return {
            'name': _('作廢應收憑單電子發票'),
            'res_model': 'action.invalid.invoice.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    # 執行電子發票作廢
    # def run_invoice_invalid(self):
    #     self.ensure_one()
    #
    #     if self.move_type != 'out_refund':
    #         raise UserError('作廢電子發票的應收憑單類型應該為客戶折讓單')
    #
    #     # 檢查是否有開立電子發票
    #     if self.III_Invoice_No:
    #         if self.III_Invoice_No.IIS_Invalid_Status == '1':
    #             raise UserError('該電子發票：%s 已作廢!!' % self.III_Invoice_No.name)
    #     else:
    #         raise UserError('找不到電子發票!!')
    #
    #     # 建立物件
    #     invoice = EcpayInvoice()
    #
    #     company_id = self.company_id
    #
    #     # 初始化物件
    #     self.ecpay_invoice_init(invoice, 'B2CInvoice/Invalid', 'Invalid', company_id)
    #
    #     # 設定電子發票作廢需要參數
    #     invoice.Send['InvoiceNo'] = self.ecpay_invoice_id.name
    #     invoice.Send['InvoiceDate'] = self.ecpay_invoice_id.IIS_Create_Date.strftime("%Y/%m/%d")
    #     invoice.Send['Reason'] = self.name
    #
    #     # 送出資訊
    #     aReturn_Info = invoice.Check_Out()
    #
    #     # 判定是否成功作廢
    #     if aReturn_Info['RtnCode'] != 1:
    #         raise UserError('作廢電子發票失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])
    #
    #     # 更新儲存在Odoo中的電子發票資訊
    #     self.ecpay_invoice_id.get_ecpay_invoice_info()

    # 執行電子發票折讓
    def run_refund(self):
        self.ensure_one()

        # 已作廢電子發票不可折讓
        if self.IA_Invoice_No.IIS_Invalid_Status == '1':
            raise UserError('已作廢的電子發票不可以再折讓')

        if self.move_type != 'out_refund':
            raise UserError('折讓電子發票的應收憑單類型應該為客戶折讓單')

        # 檢查欲折讓的發票是否有被設定
        if self.ecpay_invoice_id.id is False:
            raise UserError('找不到欲折讓的發票！')

        # 建立物件
        invoice = EcpayInvoice()

        company_id = self.company_id

        # 初始化物件
        self.ecpay_invoice_init(invoice, 'B2CInvoice/Allowance', 'ALLOWANCE', company_id)

        invoice.Send['InvoiceNo'] = self.ecpay_invoice_id.name
        invoice.Send['InvoiceDate'] = self.ecpay_invoice_id.IIS_Create_Date.strftime("%Y/%m/%d")
        invoice.Send[
            'CustomerName'] = self.partner_id.name if self.partner_id else self.ecpay_invoice_id.IIS_Customer_Name
        invoice.Send['AllowanceNotify'] = 'E'
        invoice.Send['NotifyMail'] = self.partner_id.email if self.partner_id.email else ''

        # 匯入發票種的發票明細到電子發票物件
        invoice.Send['Items'], amount_total = self.prepare_item_list()
        invoice.Send['AllowanceAmount'] = int(self.amount_total)

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否開立成功
        if aReturn_Info['RtnCode'] != 1:
            raise UserError('折讓開立失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])
        # 寫入折讓號碼
        self.IA_Allow_No = aReturn_Info['IA_Allow_No']
        self.ecpay_invoice_id.IIS_Remain_Allowance_Amt = aReturn_Info['IA_Remain_Allowance_Amt']
        self.uniform_state = 'Discounted'
        self.refund_finish = True
        if not self.IA_Invoice_No:
            self.IA_Invoice_No = self.ecpay_invoice_id.id,

    # 調用作廢折讓 Wizard
    def action_run_refund_invalid(self):
        ''' Open the account.payment.register wizard to pay the selected journal entries.
        :return: An action opening the account.payment.register wizard.
        '''
        return {
            'name': _('作廢折讓發票'),
            'res_model': 'invoice.invalid.wizard',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    # 電子發票前端驗證手機條碼ＡＰＩ
    @api.model
    def check_carrier_num(self, text):

        # 建立電子發票物件
        invoice = EcpayInvoice()

        company_id = self.env.company

        # 初始化物件
        self.ecpay_invoice_init(invoice, 'B2CInvoice/CheckBarcode', 'CheckBarcode', company_id)

        # 準備傳送參數
        invoice.Send['BarCode'] = text

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否成功
        if aReturn_Info['RtnCode'] == 1 and aReturn_Info['IsExist'] == 'Y':
            return True
        else:
            return False

    # 電子發票前端驗證愛心碼ＡＰＩ
    @api.model
    def check_lovecode(self, text):

        # 建立電子發票物件
        invoice = EcpayInvoice()

        company_id = self.env.company

        # 初始化物件
        self.ecpay_invoice_init(invoice, 'B2CInvoice/CheckLoveCode', 'CheckLoveCode', company_id)

        # 準備傳送參數
        invoice.Send['LoveCode'] = text

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 檢查是否成功
        return aReturn_Info['RtnCode'] == 1 and aReturn_Info['IsExist'] == 'Y'
