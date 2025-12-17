from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ptt_api_user = fields.Char(string='PTT API Kullanıcısı', config_parameter='ptt.api_user', default='PttWs')
    ptt_api_password = fields.Char(string='PTT API Şifre', config_parameter='ptt.api_password')
    ptt_customer_id = fields.Char(string='PTT Müşteri No', config_parameter='ptt.customer_id')
    ptt_barcode_start = fields.Char(string='PTT Barkod Başlangıç', config_parameter='ptt.barcode_start', help="Örn: 2700000000001")
    
