from odoo import models, fields, api, _

class SevendCorrespondence(models.Model):
    _name = 'sevend.correspondence'
    _description = 'Yazışmalar'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'date desc, id desc'

    name = fields.Char(string='Referans ID', required=True, copy=False, readonly=True, default='Yeni')
    type = fields.Selection([
        ('incoming', 'Gelen'),
        ('outgoing', 'Giden')
    ], string='Yazı Tipi', default='incoming', required=True)
    
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('sent', 'Gönderildi / Teslim Alındı'),
        ('replied', 'Cevaplandı'),
        ('archived', 'Arşivlendi'),
        ('cancel', 'İptal')
    ], string='Durum', default='draft', tracking=True)

    partner_id = fields.Many2one('res.partner', string='İlgili Kurum / Kişi')
    project_code = fields.Char(string='Proje Kod', help="Örn: P.87.1019")
    series = fields.Char(string='Yazı Seri', help="Örn: L25")
    department = fields.Char(string='Departman')
    document_number = fields.Char(string='Belge No')
    branch = fields.Char(string='Şube')
    date = fields.Date(string='Tarih', default=fields.Date.today)
    
    # Alıcı / Gönderici Bilgileri (Resmi Yazı İçin)
    recipient_name = fields.Char(string='Kime İsim', help="Yazının muhatabı olan makam/kişi")
    recipient_address = fields.Text(string='Kime Adres')
    recipient_email = fields.Char(string='Gönderilecek Mail Adresi')
    cc_list = fields.Char(string='CC Liste')
    
    # Konu ve İçerik (TR/EN)
    subject = fields.Char(string='Konu', required=True)
    subject_en = fields.Char(string='Konu EN')
    content = fields.Html(string='İçerik')
    content_en = fields.Html(string='İçerik EN')
    content_2 = fields.Html(string='İçerik 2')
    content_2_en = fields.Html(string='İçerik 2 EN')
    
    # İmza / Ünvan
    full_name = fields.Char(string='Ad Soyad', help="Yazıyı imzalayan yetkili")
    job_title = fields.Char(string='Ünvan')
    job_title_en = fields.Char(string='Ünvan EN')
    
    # İlgi Listesi (Reference List) - Many2many relationship with self
    reference_ids = fields.Many2many('sevend.correspondence', 'correspondence_reference_rel', 
                                     'src_id', 'dest_id', string='İlgi Tutulan Yazılar')
    reference_text = fields.Text(string='İlgi Listesi Metin')
    reference_text_en = fields.Text(string='İlgi Listesi EN')
    
    # Teknik / Linkler
    is_mail_sent = fields.Boolean(string='E-Mail Gönderildi mi?', default=False)
    sharepoint_link = fields.Char(string='Sharepoint Link')
    test_counter = fields.Integer(string='Test Sayacı')
    pdf_url = fields.Char(string='PDF URL')
    visual = fields.Binary(string='Görsel / Belge')
    attachment_ids = fields.Many2many('ir.attachment', string='Ek Dosyalar')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Yeni') == 'Yeni':
            # Use separate sequences based on type
            letter_type = vals.get('type') or 'incoming'
            seq_code = 'sevend.correspondence.incoming' if letter_type == 'incoming' else 'sevend.correspondence.outgoing'
            
            vals['name'] = self.env['ir.sequence'].next_by_code(seq_code) or 'Yeni'
        return super(SevendCorrespondence, self).create(vals)

    def action_post(self):
        """ Approve/Send the letter """
        for record in self:
            if record.state == 'draft':
                record.state = 'sent'
    
    def action_draft(self):
        """ Reset to draft """
        for record in self:
            record.state = 'draft'

    def action_reply(self):
        """ Create a new outgoing letter as a reply to this one """
        self.ensure_one()
        reply_vals = {
            'type': 'outgoing',
            'subject': 'RE: ' + (self.subject or ''),
            'subject_en': 'RE: ' + (self.subject_en or '') if self.subject_en else False,
            'recipient_name': self.recipient_name, # Usually the sender becomes the recipient
            'reference_ids': [(4, self.id)],
            'project_code': self.project_code,
            'partner_id': self.partner_id.id,
        }
        # Change state to replied
        self.state = 'replied'
        
        # Open the new record in form view
        return {
            'name': _('Cevap Yazısı Oluştur'),
            'type': 'ir.actions.act_window',
            'res_model': 'sevend.correspondence',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_type': 'outgoing', 'default_reference_ids': [(4, self.id)]},
        }

    def action_send_mail(self):
        """ E-Mail gönderme butonu """
        self.ensure_one()
        # Logic to open email composer or send directly could go here
        self.is_mail_sent = True
        return True
