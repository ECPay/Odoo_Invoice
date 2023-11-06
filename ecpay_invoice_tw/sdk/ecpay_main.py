# -*- coding: UTF-8 -*-
import time
import base64
from Crypto.Util.Padding import pad, unpad
import urllib.parse
import json
from Crypto.Cipher import AES
from odoo.addons.ecpay_invoice_tw.sdk.ecpay_setting import *
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class EcpayInvoice():
    TimeStamp = ''
    MerchantID = ''
    HashKey = ''
    HashIV = ''
    Send = 'Send'
    Invoice_Method = 'INVOICE'  # 電子發票執行項目
    Invoice_Url = 'Invoice_Url'  # 電子發票執行網址

    def __init__(self):
        self.Send = dict()
        self.Send['RelateNumber'] = ''
        self.Send['CustomerID'] = ''
        self.Send['CustomerIdentifier'] = ''
        self.Send['CustomerName'] = ''
        self.Send['CustomerAddr'] = ''
        self.Send['CustomerPhone'] = ''
        self.Send['CustomerEmail'] = ''
        self.Send['ClearanceMark'] = ''
        self.Send['Print'] = EcpayPrintMark.No
        self.Send['Donation'] = EcpayDonation.No
        self.Send['LoveCode'] = ''
        self.Send['CarrierType'] = ''
        self.Send['CarrierNum'] = ''
        self.Send['TaxType'] = ''
        self.Send['SalesAmount'] = ''
        self.Send['InvoiceRemark'] = ''
        self.Send['Items'] = list()
        self.Send['InvType'] = ''
        self.Send['vat'] = EcpayVatType.Yes
        self.Send['DelayFlag'] = ''
        self.Send['DelayDay'] = 0
        self.Send['Tsr'] = ''
        self.Send['PayType'] = ''
        self.Send['PayAct'] = ''
        self.Send['NotifyURL'] = ''
        self.Send['InvoiceNo'] = ''
        self.Send['AllowanceNotify'] = ''
        self.Send['NotifyMail'] = ''
        self.Send['NotifyPhone'] = ''
        self.Send['AllowanceAmount'] = ''
        self.Send['InvoiceNumber'] = ''
        self.Send['Reason'] = ''
        self.Send['AllowanceNo'] = ''
        self.Send['Phone'] = ''
        self.Send['Notify'] = ''
        self.Send['InvoiceTag'] = ''
        self.Send['Notified'] = ''
        self.Send['BarCode'] = ''
        self.Send['ReturnURL '] = ''
        self.Send['OnLine'] = True
        self.TimeStamp = int(time.time())

    def Check_Out(self):
        arParameters = self.Send.copy()
        arParameters['MerchantID'] = self.MerchantID
        arParameters['TimeStamp'] = self.TimeStamp
        return ECPay_Invoice_Send.CheckOut(arParameters, self.HashKey, self.HashIV, self.Invoice_Method,
                                           self.Invoice_Url)


'''
送出資訊
'''


class ECPay_Invoice_Send():
    # 發票物件
    InvoiceObj = ''
    InvoiceObj_Return = ''

    '''
    背景送出資料
    '''

    @staticmethod
    def cbc_encrypt(self, plaintext, key, iv):
        """
        AES-CBC 加密
        key 必須是 16(AES-128)、24(AES-192) 或 32(AES-256) 位元組的 AES 金鑰；
        初始化向量 iv 為隨機的 16 位字串 (必須是16位)，
        解密需要用到這個相同的 iv，因此將它包含在密文的開頭。
        """
        url_encoded_padded = pad(plaintext.encode(), AES.block_size)
        cipher = AES.new(bytes(key, 'utf-8'), AES.MODE_CBC, bytes(iv, 'utf-8'))
        _logger.info('random IV : ', base64.b64encode(cipher.iv).decode('utf-8'))
        data_check = cipher.encrypt(url_encoded_padded)
        data_base64_encoded = base64.b64encode(data_check).decode()
        return data_base64_encoded

    @staticmethod
    def cbc_decrypt(self, ciphertext, key, iv):
        # 對data進行AES解密
        decrypt_cipher = AES.new(bytes(key, 'utf-8'), AES.MODE_CBC, bytes(iv, 'utf-8'))
        base64_decoded = base64.b64decode(ciphertext)
        decrypted = decrypt_cipher.decrypt(base64_decoded)
        # 對解密後的數據進行解填充
        decrypted_unpadded = unpad(decrypted, AES.block_size)
        # 對解填充後的數據進行urldecode
        url_decoded = urllib.parse.unquote(decrypted_unpadded.decode())
        # 輸出解密後的數據
        _logger.info(url_decoded)
        return url_decoded

    @staticmethod
    def CheckOut(arParameters=dict, HashKey='', HashIV='', Invoice_Method='', ServiceURL=''):
        MerchantID = arParameters['MerchantID']
        arParameters = ECPay_Invoice_Send.process_send(arParameters, HashKey, HashIV, Invoice_Method, ServiceURL)
        sz_Result = ECPay_Invoice_Send.process_data(arParameters, MerchantID, HashKey, HashIV, ServiceURL)
        # # 回傳資訊處理將字串 轉換為 json
        sz_ReturnInfo = json.loads(sz_Result)
        return sz_ReturnInfo

    def process_data(self, MerchantID, HashKey, HashIV, url):
        headers = {"Content-Type": "application/json"}
        data_json = json.dumps(self)
        #  將 Data資料進行 url encode編碼 在送進AES加密
        data_encoded = urllib.parse.quote(data_json)
        cipher = ECPay_Invoice_Send.cbc_encrypt(self, data_encoded, HashKey, HashIV)
        transaction_data_array = json.dumps({
            'MerchantID': MerchantID,
            'RqHeader': {
                'Timestamp': self.get('TimeStamp') if self.get('TimeStamp') else int(time.time()),
            },
            'Data': cipher,
        })
        try:
            data_response = requests.post(url, transaction_data_array, headers=headers, timeout=120)
            #  檢查狀態碼是否為基本要求的 status_code = 200
            if data_response.status_code != 200:
                raise UserError(f'HTTP status code exception: ' + str(data_response.status_code))
            result_data = json.loads(data_response.text)
            if result_data.get('TransCode') != 1 or result_data.get('TransMsg') != 'Success':
                raise UserError(f'串接電子發票失敗!!錯誤訊息： ' + str(result_data.get('TransMsg')))
            # 從result_data中取出"Data" 加密字段
            encrypted_data = result_data.get("Data")
            decrypted_data = ECPay_Invoice_Send.cbc_decrypt(self, encrypted_data, HashKey, HashIV)
            return decrypted_data
        except Exception as e:
            raise UserError(f'Exception: ' + str(e))

    # 資料檢查與過濾(送出)
    @staticmethod
    def process_send(arParameters=dict, HashKey='', HashIV='', Invoice_Method='', ServiceURL='',
                     return_exception=False):
        # 宣告物件
        InvoiceMethod = 'ECPay_' + Invoice_Method
        if InvoiceMethod in globals():
            class_str = globals()[InvoiceMethod]
            InvoiceObj = class_str()
        else:
            raise UserError(f'Invoice_Method錯誤: ' + str(Invoice_Method))
        arException = InvoiceObj.check_exception(arParameters)
        return arException


# 抽象化 類別，將所有的ECPay_XXX類別的共用方法抽出來
class ECPay_Base:
    parameters = {}
    none_verification = {}

    def insert_string(self, arParameters=dict):
        # common implementation
        pass

    def check_extend_string(self, arParameters=dict):
        # common implementation
        pass

    def check_exception(self, arParameters=dict):
        # common implementation
        pass

    @classmethod
    def requires_check_mac_value(cls):
        return False


'''
*  A一般開立 
'''


class ECPay_INVOICE(ECPay_Base):
    # 所需參數
    def check_exception(self, arParameters=dict):
        if 'CarrierNum' in arParameters:
            # 載具編號內包含 + 號則改為空白
            arParameters['CarrierNum'] = arParameters['CarrierNum'].replace('+', ' ')
        return arParameters

    '''
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return True


'''
*  B 開立折讓
'''


class ECPay_ALLOWANCE(ECPay_Base):
    # 所需參數
    parameters = dict({
        'MerchantID': '',
        'InvoiceNo': '',
        'InvoiceDate': '',
        'AllowanceNotify': '',
        'CustomerName': '',
        'NotifyMail': '',
        'NotifyPhone': '',
        'AllowanceAmount': '',
        'Items': list(),
        'ItemName': '',
        'ItemCount': '',
        'ItemWord': '',
        'ItemPrice': '',
        'ItemTaxType': '',
        'ItemAmount': '',
    })

    def check_exception(self, arParameters=dict):
        arParameters = {k: v for k, v in arParameters.items() if k in self.parameters}
        return arParameters

    '''
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return False


'''
*  C 發票作廢
'''


class ECPay_Invalid(ECPay_Base):
    # 所需參數
    parameters = dict({
        'MerchantID': '',
        'InvoiceNo': '',
        'InvoiceDate': '',
        'Reason': ''
    })

    def check_exception(self, arParameters=dict):
        arParameters = {k: v for k, v in arParameters.items() if k in self.parameters}
        return arParameters

    '''
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return False


'''
*  D 折讓作廢
'''


class ECPay_AllowanceInvalid(ECPay_Base):
    # 所需參數
    parameters = dict({
        'MerchantID': '',
        'InvoiceNo': '',
        'AllowanceNo': '',
        'Reason': '',
    })

    def check_exception(self, arParameters=dict):
        arParameters = {k: v for k, v in arParameters.items() if k in self.parameters}
        return arParameters

    '''
    
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return False


'''
*  E 查詢發票
'''


class ECPay_INVOICE_SEARCH(ECPay_Base):
    # 所需參數
    parameters = dict({
        'RelateNumber': '',
    })

    def check_exception(self, arParameters=dict):
        arParameters = {k: v for k, v in arParameters.items() if k in self.parameters}
        return arParameters

    '''
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return False


'''
*  L手機條碼驗證
'''


class ECPay_CheckBarcode(ECPay_Base):
    # 所需參數
    parameters = dict({
        'MerchantID': '',
        'BarCode': ''
    })

    def check_exception(self, arParameters=dict):
        arParameters = {k: v for k, v in arParameters.items() if k in self.parameters}
        return arParameters

    '''
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return False


'''
*  M愛心碼驗證
'''


class ECPay_CheckLoveCode(ECPay_Base):
    # 所需參數
    parameters = dict({
        'MerchantID': '',
        'LoveCode': '',
    })

    def check_exception(self, arParameters=dict):
        arParameters = {k: v for k, v in arParameters.items() if k in self.parameters}
        return arParameters

    '''
    *  返回是否壓碼執行
    '''

    @classmethod
    def requires_check_mac_value(cls):
        return False

