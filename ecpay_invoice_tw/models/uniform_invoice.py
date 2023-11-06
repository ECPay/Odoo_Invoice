# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import datetime
import random

from odoo import models, fields
from odoo.addons.ecpay_invoice_tw.sdk.ecpay_main import *

tax_sign = {
    '1': 'TX',
    '2': 'ZX',
    '3': ''
}


class UniformInvoice(models.Model):
    _name = 'uniform.invoice'

    name = fields.Char(string='統一發票號碼')
    related_number = fields.Char(default=lambda self: 'ECPAY' + time.strftime("%Y%m%d%H%M%S", time.localtime()) +
                                                      str(random.randint(1000000000, 2147483647)), readonly=True)
    IIS_Award_Flag = fields.Selection(string='中獎旗標',
                                      selection=[('0', '未中獎'), ('1', '已中獎'), ('X', '有統編之發票')])
    IIS_Award_Type = fields.Selection(string='中獎種類',
                                      selection=[('0', '未中獎'), ('6', '六獎 二百元'), ('5', '五獎 一千元'),
                                                 ('4', '四獎 四千元'), ('3', '三獎 一萬元'), ('2', '二獎 四萬元'),
                                                 ('1', '頭獎 二十萬元'), ('7', '特獎 二百萬元'), ('8', '特別獎 一千萬'),
                                                 ('9', '無實體2000元獎'), ('10', '無實體百萬元獎')])
    IIS_Carrier_Num = fields.Char(string='載具編號')
    IIS_Carrier_Type = fields.Selection(string='載具類別',
                                        selection=[('1', '綠界科技電子發票載具'), ('2', '消費者自然人憑證'),
                                                   ('3', '消費者手機條碼')])
    IIS_Category = fields.Selection(string='發票類別', selection=[('B2B', '有統編'), ('B2C', '無統編')])
    IIS_Check_Number = fields.Char(string='發票檢查碼')
    IIS_Clearance_Mark = fields.Selection(string='通關方式', selection=[('1', '經海關出口'), ('2', '非經海關出口')])
    IIS_Create_Date = fields.Datetime(string='發票開立時間')
    IIS_Customer_Addr = fields.Char(string='客戶地址')
    IIS_Customer_Email = fields.Char(string='客戶電子信箱')
    IIS_Customer_ID = fields.Char(string='客戶編號')
    IIS_Customer_Name = fields.Char(string='客戶名稱')
    IIS_Customer_Phone = fields.Char(string='客戶電話')
    IIS_Identifier = fields.Char(string='買方統編')
    IIS_Invalid_Status = fields.Selection(string='發票作廢狀態', selection=[('1', '已作廢'), ('0', '未作廢')])
    IIS_IP = fields.Char(string='發票開立IP')
    IIS_Issue_Status = fields.Selection(string='發票開立狀態', selection=[('1', '發票開立'), ('0', '發票註銷')])
    IIS_Love_Code = fields.Char(string='捐款單位捐贈碼')
    IIS_Mer_ID = fields.Char(string='合作特店編號')
    IIS_Number = fields.Char(string='發票號碼')
    IIS_Print_Flag = fields.Selection(string='列印旗標', selection=[('1', '列印'), ('0', '不列印')])
    IIS_Random_Number = fields.Char(string='隨機碼')
    IIS_Relate_Number = fields.Char(string='合作特店自訂編號')
    IIS_Remain_Allowance_Amt = fields.Char(string='剩餘可折讓金額')
    IIS_Sales_Amount = fields.Char(string='發票金額')
    IIS_Tax_Amount = fields.Char(string='稅金')
    IIS_Tax_Rate = fields.Char(string='稅率')
    IIS_Tax_Type = fields.Selection(string='課稅別',
                                    selection=[('1', '應稅'), ('2', '零稅率'), ('3', '免稅'), ('9', '混合應稅與免稅')])
    IIS_Turnkey_Status = fields.Selection(string='發票上傳後接收狀態',
                                          selection=[('C', '成功'), ('E', '失敗'), ('G', '處理中')])
    IIS_Type = fields.Selection(string='發票種類', selection=[('07', '一般稅額計算'), ('08', '特種稅額計算')])
    IIS_Upload_Date = fields.Datetime(string='發票上傳時間')
    IIS_Upload_Status = fields.Selection(string='發票上傳狀態', selection=[('1', '已上傳'), ('0', '未上傳')])
    InvoiceRemark = fields.Char(string='發票備註')
    ItemAmount = fields.Char(string='商品合計')
    ItemCount = fields.Char(string='商品數量')
    ItemName = fields.Char(string='商品名稱')
    ItemPrice = fields.Char(string='商品價格')
    ItemRemark = fields.Char(string='商品備註說明')
    ItemTaxType = fields.Char(string='商品課稅別')
    ItemWord = fields.Char(string='商品單位')
    PosBarCode = fields.Char(string='顯示電子發票BARCODE用')
    QRCode_Left = fields.Char(string='顯示電子發票QRCODE左邊用')
    QRCode_Right = fields.Char(string='顯示電子發票QRCODE右邊用')
    RtnCode = fields.Char(string='回應代碼')
    RtnMsg = fields.Char(string='回應訊息')
    CheckMacValue = fields.Char(string='檢查碼')
    SpecialTaxType = fields.Integer(string='特種稅額計算之課稅別')
    invoice_month = fields.Char(string='發票月份')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False)
    ChannelPartner = fields.Char(string='通路商代號')

    # Odoo都是使用GMT標準時間來儲存
    # def trasfer_time(self, time_before):
    #     # time_after = (datetime.datetime.strptime(time_before, '%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    #     time_after = datetime.datetime.strptime(time_before, '%Y-%m-%d %H:%M:%S')
    #     return time_after

    # 向綠界後台取得電子發票的詳細資訊
    def get_ecpay_invoice_info(self):
        self.ensure_one()

        invoice = EcpayInvoice()
        move = self.env['account.move'].search([('ecpay_invoice_id', '=', self.id), ('move_type', '=', 'out_invoice')],
                                               limit=1)
        move.ecpay_invoice_init(invoice, 'B2CInvoice/GetIssue', 'INVOICE_SEARCH')
        invoice.Send['RelateNumber'] = self.related_number
        aReturn_Info = invoice.Check_Out()

        if aReturn_Info['RtnCode'] != 1:
            raise UserError('查詢發票失敗!!' + aReturn_Info['RtnMsg'])

        processed_return_info = self.process_return_info(aReturn_Info)
        # 設定發票的日期
        invoice_create = datetime.datetime.strptime(processed_return_info['IIS_Create_Date'], '%Y-%m-%d+%H:%M:%S')
        processed_return_info['IIS_Create_Date'] = datetime.datetime.strptime(processed_return_info['IIS_Create_Date'],
                                                                              '%Y-%m-%d+%H:%M:%S')
        processed_return_info['IIS_Create_Date'] -= datetime.timedelta(hours=8)
        processed_return_info['IIS_Upload_Date'] = datetime.datetime.strptime(processed_return_info['IIS_Upload_Date'],
                                                                              '%Y-%m-%d+%H:%M:%S')
        processed_return_info['IIS_Upload_Date'] -= datetime.timedelta(hours=8)
        processed_return_info['IIS_Customer_Addr'] = processed_return_info['IIS_Customer_Addr'].replace('\n',
                                                                                                        ' ').replace(
            "+", " ")
        date = invoice_create.date()
        datetime_int = int(invoice_create.strftime("%m"))
        if datetime_int == 11 or datetime_int == 12:
            self.invoice_month = str(date.year - 1911) + '年11-12月'
        elif datetime_int % 2 == 0:
            self.invoice_month = str(date.year - 1911) + '年0' + str(datetime_int - 1) + '-' + invoice_create.strftime(
                "%m") + '月'
        elif datetime_int % 2 == 1:
            self.invoice_month = str(date.year - 1911) + '年' + invoice_create.strftime("%m") + '-0' + str(
                datetime_int + 1) + '月'

        self.write(processed_return_info)

    def process_return_info(self, arParameters=dict):
        nItems_Count_Total = 0
        nItems_Foreach_Count = 1
        sItemName = ''
        sItemCount = ''
        sItemWord = ''
        sItemPrice = ''
        sItemTaxType = ''
        sItemAmount = ''
        sItemRemark = ''

        # Python特性，需要複製一個字典，不然回修改到原先宣告的字典的key與value
        parameters = arParameters.copy()

        for key, val in parameters.items():
            if key in arParameters:
                parameters[key] = arParameters[key]
        # 商品資訊組合
        nItems_Count_Total = len(arParameters['Items'])  # 商品總筆數
        if nItems_Count_Total != 0:
            for val2 in arParameters['Items']:
                sItemName += val2['ItemName'] if 'ItemName' in val2 else ''
                sItemCount += str(val2['ItemCount'])
                sItemWord += val2['ItemWord'] if 'ItemWord' in val2 else ''
                sItemPrice += str(val2['ItemPrice'])
                sItemTaxType += str(val2['ItemTaxType']) if 'ItemTaxType' in val2 else ''
                sItemAmount += str(val2['ItemAmount'])
                sItemRemark += val2['ItemRemark'] if 'ItemRemark' in val2 else ''

                if nItems_Foreach_Count < nItems_Count_Total:
                    sItemName += '|'
                    sItemCount += '|'
                    sItemWord += '|'
                    sItemPrice += '|'
                    sItemTaxType += '|'
                    sItemAmount += '|'
                    sItemRemark += '|'
                nItems_Foreach_Count += 1
        parameters['ItemName'] = sItemName  # 商品名稱
        parameters['ItemCount'] = sItemCount
        parameters['ItemWord'] = sItemWord  # 商品單位
        parameters['ItemPrice'] = sItemPrice
        parameters['ItemTaxType'] = sItemTaxType
        parameters['ItemAmount'] = sItemAmount
        parameters['ItemRemark'] = sItemRemark  # 商品備註

        del parameters['Items']
        return parameters

    def split_order_line(self):
        self.ensure_one()

        lines = []
        ItemAmount = self.ItemAmount.split('|')
        ItemCount = self.ItemCount.split('|')
        ItemName = self.ItemName.split('|')
        ItemPrice = self.ItemPrice.split('|')
        ItemRemark = self.ItemRemark.split('|')
        ItemTaxType = self.ItemTaxType.split('|')
        ItemWord = self.ItemWord.split('|')
        for item in zip(ItemAmount, ItemCount, ItemName, ItemPrice, ItemRemark, ItemTaxType, ItemWord):
            line = {
                'ItemAmount': item[0],
                'ItemCount': item[1],
                'ItemName': item[2],
                'ItemPrice': item[3],
                'ItemRemark': item[4],
                'ItemTaxSign': tax_sign.get(item[5]),
                'ItemWord': item[6],
            }
            lines.append(line)
        return lines

    def count_order_line(self) -> int:
        if not self:
            return 0

        try:
            self.ensure_one()
        except ValueError:
            self = self[0]

        return len(self.ItemAmount.split('|'))
