import logging
import requests
import datetime
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ptt_barcode = fields.Char(string='PTT Barkod', copy=False, help="PTT Kargo Barkod Numarası")
    ptt_tracking_number = fields.Char(string='PTT Takip No', copy=False)
    ptt_status = fields.Selection([
        ('draft', 'Gönderilmedi'),
        ('sent', 'PTT\'ye İletildi'),
        ('error', 'Hata'),
    ], string='PTT Durumu', default='draft', copy=False)
    ptt_error_message = fields.Text(string='PTT Hata Mesajı', copy=False)

    def _get_ptt_credentials(self):
        params = self.env['ir.config_parameter'].sudo()
        user = params.get_param('ptt.api_user')
        password = params.get_param('ptt.api_password')
        cust_id = params.get_param('ptt.customer_id')
        return user, password, cust_id

    def generate_ptt_barcode(self):
        self.ensure_one()
        # Sequence logic typically handled by valid config or ir.sequence.
        # Here we use a simpler approach: reading next number from config if sequence not set up
        # Ideally, user should setup an ir.sequence for 'PTT Barcode'
        # For this implementation I will simply fetch the start and increment.
        # NOTE: A real efficient way uses ir.sequence. I will implement a basic autoincrement here.
        params = self.env['ir.config_parameter'].sudo()
        current_barcode = params.get_param('ptt.barcode_current')
        start_barcode = params.get_param('ptt.barcode_start')
        
        if not current_barcode:
            current_barcode = start_barcode
            
        if not current_barcode:
            raise UserError(_("Lütfen PTT Barkod Başlangıç değerini ayarlarda belirtin."))
            
        # Calculation validation (PTT barcodes are 13 chars usually).
        # We assume numerical increment works.
        try:
             # Basic check if it ends with TR or not, usually just digits for API generation range? 
             # PTT usually gives a range like 2700000000001 - 2700000000999.
             # We just increment the integer part.
             # If it has TR suffix, we might need to handle it. Assuming pure digits as per PHP example implication (which treats it as string but auto-generates).
             next_val = int(current_barcode)
             self.ptt_barcode = str(next_val)
             params.set_param('ptt.barcode_current', str(next_val + 1))
        except ValueError:
             # If alphanumeric, just use as is (User must manage manually or custom logic needed)
             self.ptt_barcode = current_barcode

    def action_send_to_ptt(self):
        for picking in self:
            if picking.state != 'done':
                 raise UserError(_("Sadece tamamlanmış (done) teslimatlar PTT'ye gönderilebilir."))

            user, password, cust_id = picking._get_ptt_credentials()
            if not (user and password and cust_id):
                raise UserError(_("PTT API ayarları eksik. Lütfen yapılandırın."))

            if not picking.ptt_barcode:
                picking.generate_ptt_barcode()

            partner = picking.partner_id
            if not partner:
                raise UserError(_("Teslimat adresi (Partner) seçili değil."))

            # Prepare Data
            # Map receiver info
            receiver_name = partner.name or ""
            address = (partner.street or "") + " " + (partner.street2 or "")
            city = partner.state_id.name or ""
            district = partner.city or "" # Odoo 'city' field often used for district or city depending on localization.
            phone = partner.phone or partner.mobile or ""
            phone = ''.join(filter(str.isdigit, phone)) # Clean phone

            # Map package info (simplified for scope)
            weight = picking.shipping_weight or 1.0
            desi = 1 # Default desi calculation logic can be complex
            
            # Should be controlled by delivery method, but for now fixed or from picking
            payment_method = 'MH' # MH: Sender Pays, UA: Receiver Pays. Defaulting to MH.
            
            # Construct XML
            # Note: The namespace prefixes must match what the server expects.
            # Based on WSDL: targetNamespace="http://kabul.ptt.gov.tr" -> xmlns:ns
            # Input2 is in "http://kabul.ptt.gov.tr/xsd" -> xmlns:ax22 (or similar)
            
            # Let's try the structure from standard PTT integrations.
            soap_body = f"""
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:kab="http://kabul.ptt.gov.tr" xmlns:xsd="http://kabul.ptt.gov.tr/xsd">
   <soapenv:Header/>
   <soapenv:Body>
      <kab:kabulEkle2>
         <kab:input>
            <xsd:dosyaAdi>{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{picking.id}</xsd:dosyaAdi>
            <xsd:kullanici>{user}</xsd:kullanici>
            <xsd:musteriId>{cust_id}</xsd:musteriId>
            <xsd:sifre>{password}</xsd:sifre>
            <xsd:dongu>
               <xsd:aAdres>{address[:200]}</xsd:aAdres>
               <xsd:agirlik>{weight}</xsd:agirlik>
               <xsd:aliciAdi>{receiver_name[:100]}</xsd:aliciAdi>
               <xsd:aliciIlAdi>{city}</xsd:aliciIlAdi>
               <xsd:aliciIlceAdi>{district}</xsd:aliciIlceAdi>
               <xsd:aliciSms>{phone}</xsd:aliciSms>
               <xsd:barkodNo>{picking.ptt_barcode}</xsd:barkodNo>
               <xsd:boy>10</xsd:boy>
               <xsd:deger_ucreti>0</xsd:deger_ucreti>
               <xsd:desi>{desi}</xsd:desi>
               <xsd:en>10</xsd:en>
               <xsd:musteriReferansNo>{picking.name}</xsd:musteriReferansNo>
               <xsd:odemesekli>{payment_method}</xsd:odemesekli>
               <xsd:odeme_sart_ucreti>0</xsd:odeme_sart_ucreti>
               <xsd:yukseklik>10</xsd:yukseklik>
               <xsd:gonderiTur>KARGO</xsd:gonderiTur>
               <xsd:gonderiTip>NORMAL</xsd:gonderiTip>
            </xsd:dongu>
         </kab:input>
      </kab:kabulEkle2>
   </soapenv:Body>
</soapenv:Envelope>
            """
            
            headers = {
                'Content-Type': 'text/xml; charset=utf-8',
                'SOAPAction': 'urn:kabulEkle2' 
            }
            
            try:
                response = requests.post(
                    "https://pttws.ptt.gov.tr/PttVeriYukleme/services/Sorgu", 
                    data=soap_body.encode('utf-8'), 
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    # Basic XML parsing to check success
                    # In a real app, use lxml or xml.etree to parse Output2
                    if "hataKodu>1<" in response.text or "hataKodu>1<" in response.content.decode('utf-8'): 
                        # 1 usually means Success in PTT (Need to verify, PHP says 1)
                        picking.ptt_status = 'sent'
                        picking.ptt_tracking_number = picking.ptt_barcode # Often same, or returned in response
                        
                        # Parse return dongu for actual barcode if generated by server?
                        # PTT usually uses the barcode we sent.
                        
                        picking.message_post(body=f"PTT'ye başarıyla gönderildi. Barkod: {picking.ptt_barcode}")
                    else:
                        picking.ptt_status = 'error'
                        picking.ptt_error_message = f"API Hatası: {response.text[:500]}"
                        picking.message_post(body=f"PTT Gönderim Hatası: {response.text[:200]}")
                else:
                    picking.ptt_status = 'error'
                    picking.ptt_error_message = f"HTTP Hatası: {response.status_code} - {response.text}"
            except Exception as e:
                picking.ptt_status = 'error'
                picking.ptt_error_message = str(e)
                _logger.error(f"PTT API connection error: {e}")
