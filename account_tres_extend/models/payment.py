# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PaiementChequeClient(models.Model):
    _inherit = 'paiement.cheque.client'

    engagement_id = fields.Binary('Engagement')
    in_name_of_id = fields.Many2one('res.partner', 'Au nom de')
    pc_id = fields.Binary('Photocopie du chèque')
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]}, default=lambda self: self.env.ref('account_tres_customer.account_journal_data_chp'))
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]}, default=fields.date.today())
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse', default=lambda self: self.env.user.caisse_id)
    model_id = fields.Many2one('paiement.pec.model.client', string=u'Modèle Comptable',
                               required=True, states={'payed': [('readonly', True)]}, default=lambda self: self.env.ref('account_tres_customer.paiement_cheque_model_client1'))
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]}, default=fields.date.today())
    accord_ids = fields.Many2many('accord.cheque.client', string='Accord Chèque')

    @api.model
    def create(self, vals):
        missing = []
        if vals.get('in_name_of_id', False):
            if vals['in_name_of_id'] != vals['client'] and not vals.get('engagement_id', False):
                missing.append("<li id='checklist-id-1'><p>Engagement</p></li>")
        if not vals.get('pc_id', False):
            missing.append("<li id='checklist-id-1'><p>Photocopie du chèque</p></li>")
        res = super(PaiementChequeClient, self).create(vals)
        client_id = self.env['res.partner'].browse(vals['client'])
        if missing:
            res.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Champs à renseigner pour le chèque du numéro ' + vals['name'] + ' du patient ' + client_id.name,
                note="<ul class='o_checklist'>" +
                     ' '.join(missing)
                     + "</ul>",
                user_id=self.env.user.id)
        return res


class AccordChequeClient(models.Model):
    _name = 'accord.cheque.client'

    name = fields.Char('Nom')
    color = fields.Integer('Color Index')


class PaiementCashClient(models.Model):
    _inherit = 'paiement.cash.client'

    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]}, default=lambda self: self.env['account.journal'].search([('name', 'like', 'Esp%')]))
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse', default=lambda self: self.env.user.caisse_id)
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]}, default=fields.date.today())


