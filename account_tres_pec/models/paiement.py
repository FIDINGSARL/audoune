# -*- coding: utf-8 -*-
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PaiementEffetModelClient(models.Model):
    _name = 'paiement.pec.model.client'
    _description = "Modele Prise en charge Client"

    name = fields.Char(string='Nom', required=True)
    company_id = fields.Many2one('res.company', string=u'Société',
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.pec.model.client'))
    received_account = fields.Many2one('account.account', string=u'Compte: PES Client à recevoir', required=True)
    at_bank_account = fields.Many2one('account.account', string=u"Compte: PES à l'encaissement", required=True)
    bank_account = fields.Many2one('account.account', string=u"Compte: Banque", required=True)
    bank_journal_id = fields.Many2one('account.journal', string=u"Journal: Banque")

    post = fields.Boolean(string=u'A Poster', default=True)


class PaiementpecClient(models.Model):
    _name = 'paiement.pec.client'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    _description = 'PEC Client'
    _order = "date desc"

    name = fields.Char(string=u'Numéro', required=True, states={'payed': [('readonly', True)]})
    amount = fields.Float(string=u'Montant', required=True, states={'payed': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]})
    model_id = fields.Many2one('paiement.pec.model.client', string=u'Modèle Comptable',
                               required=True, states={'payed': [('readonly', True)]})
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]})
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]})
    at_bank_date = fields.Date(u'Date encaissement')
    payed_date = fields.Date(u'Date encaissé/rejet')
    note = fields.Text("Notes")
    bank_client = fields.Many2one("res.partner.bank", string="Banque client")
    client = fields.Many2one('res.partner', string='Client', required=True, states={'payed': [('readonly', True)]})
    move_line_ids = fields.One2many('account.move.line', 'pec_client_id',
                                    string=u'Lignes Comptables', states={'payed': [('readonly', True)]})
    tres_fees_ids = fields.One2many('tres.fees', 'effet_client_id', string=u'Frais Bancaires')
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse')
    paiement_record_id = fields.Many2one('paiement.record', string=u'Reçu de Paiement', ondelete='cascade')
    company_id = fields.Many2one('res.company', u'Société', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'paiement.pec.client'))
    reco_amount = fields.Float(string=u'Montant lettré')
    analytic_account_id = fields.Many2one('account.analytic.account', string=u'Compte Analytique',
                                          states={'payed': [('readonly', True)]})
    rejete = fields.Boolean(string=u"Rejeté", copy=False, readonly=True, default=False)
    pec_origin_id = fields.Many2one('paiement.pec.client', string=u'Chèque Origine', readonly=True)
    origin = fields.Char('Origine')
    state = fields.Selection([('draft', u'Brouillon'),
                              ('caisse', u'Caisse'),
                              ('caisse_centrale', u'Caisse centrale'),
                              ('received', u'Bordereau'),
                              ('at_bank', u'Encaissement'),
                              ('payed', u'Encaissé'),
                              ('cancel', u'Annulé'),
                              ('rejected', u'Rejeté'),
                              ('to_represent', u'Représenté'),
                              ('to_change', u'Changé')], 'Etat', default='draft', readonly=True, required=True)
    assurance_id = fields.Many2one('pec.assurance', string="Assurance client")

    def unlink(self):
        for rec in self:
            move_ids = rec.move_line_ids.mapped('move_id')
            move_ids.button_cancel()
            move_ids.unlink()
        return super(PaiementpecClient, self).unlink()

    def action_post_fees(self):
        for pec in self:
            for fees in pec.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'state': 'draft',
            'move_line_ids': [],
            'paiement_record_id': False,
        })
        return super(PaiementpecClient, self).copy(default)

    @api.model
    def get_partner_account(self, part, type):
        account_id = False
        if part and part.id:
            account_id = part.property_account_receivable_id.id
        return account_id

    def action_post_entries(self):
        account_move_obj = self.env['account.move']
        for pec in self:
            journal_id = pec.journal_id
            analytic = False
            # date = fields.Date.context_today(self)
            date = datetime.now()
            if pec.state == 'draft':
                date = pec.date
                account_id = self.get_partner_account(pec.client, 'client')
                if not account_id:
                    raise UserError(u'Le partenaire doit avoir un compte comptable')
                if pec.analytic_account_id:
                    analytic = pec.analytic_account_id.id
                deb_account = pec.model_id.received_account.id
                cred_account = account_id
            if pec.state == 'received':
                if pec.bordereau_id:
                    date = pec.bordereau_id.date
                deb_account = pec.model_id.at_bank_account.id
                cred_account = pec.model_id.received_account.id
            if pec.state == 'at_bank':
                date = pec.payed_date
                journal_id = pec.bordereau_id.journal_id
                deb_account = journal_id.default_account_id.id
                cred_account = pec.model_id.at_bank_account.id

            debit_val = {
                'name': pec.name,
                'date': date,
                'date_maturity': pec.due_date,
                'ref': pec.note,
                'partner_id': pec.client.id,
                'account_id': deb_account,
                'credit': 0.0,
                'debit': pec.amount,
                'pec_client_id': pec.id,
                'journal_id': journal_id.id,
                'currency_id': False
            }

            credit_val = {
                'name': pec.name,
                'date': date,
                'date_maturity': pec.due_date,
                'ref': pec.note,
                'partner_id': pec.client.id,
                'account_id': cred_account,
                'credit': pec.amount,
                'debit': 0.0,
                'pec_client_id': pec.id,
                'journal_id': journal_id.id,
                'analytic_account_id': analytic,
                'currency_id': False
            }

            lines = [(0, 0, debit_val), (0, 0, credit_val)]
            pec_name = pec.name
            if pec.state == 'received':
                pec_name = pec.name + '[BORD]'
            elif pec.state == 'at_bank':
                pec_name = pec.name + '[ENC]'
            elif pec.state == 'rejected':
                pec_name = pec.name + '[REP]'
            move_id = account_move_obj.create({
                'journal_id': journal_id.id,
                'date': date,
                'name': pec_name,
                'ref': pec.note,
                # 'type': 'entry',
                'line_ids': lines,
            })
            move_id.post()
        return True

    def action_caisse(self):
        for pec in self:
            if pec.model_id.post:
                self.action_post_entries()
            pec.write({'state': 'caisse'})
        return True

    def action_caisse_centrale(self):
        caisse_obj = self.env['paiement.caisse']
        for pec in self:
            caisse_id = caisse_obj.search([('caisse_centrale', '=', True)], limit=1)
            if not caisse_id:
                raise UserError(u"Vous devez créer une caisse centrale")
            pec.write({'caisse_id': caisse_id.id, 'state': 'caisse_centrale'})
        return True

    def action_received(self):
        self.write({'state': 'received'})
        if not self.bordereau_id:
            raise ValidationError(u'Veuillez renseigner le bordereau de chèque')
        return True

    def action_at_bank(self):
        for pec in self:
            if self.model_id.post:
                self.action_post_entries()
            pec.write({'state': 'at_bank', 'at_bank_date': fields.Date.context_today(self)})
        return True

    def action_payed(self):
        for pec in self:
            if not pec.payed_date:
                payed_date = fields.Date.context_today(self)
            else:
                payed_date = pec.payed_date
            pec.write({'payed_date': payed_date})
            if pec.model_id.post:
                self.action_post_entries()
            pec.write({'state': 'payed'})
        return True

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def create_accounting_lines(self, pec, debit_account, credit_account):
        date = fields.Date.context_today(self)

        if not pec.payed_date:
            payed_date = fields.Date.context_today(self)
        else:
            payed_date = pec.payed_date
        pec.write({'payed_date': payed_date})

        debit_val = {
            'name': pec.name,
            'date': date,
            'date_maturity': pec.due_date,
            'ref': pec.note,
            'partner_id': pec.client.id,
            'account_id': debit_account,
            'credit': 0.0,
            'debit': pec.amount,
            'pec_client_id': pec.id,
            'journal_id': pec.journal_id.id,
            'currency_id': False
        }

        credit_val = {
            'name': pec.name,
            'date': date,
            'date_maturity': pec.due_date,
            'ref': pec.note,
            'partner_id': pec.client.id,
            'account_id': credit_account,
            'credit': pec.amount,
            'debit': 0.0,
            'pec_client_id': pec.id,
            'journal_id': pec.journal_id.id,
            'analytic_account_id': False,
            'currency_id': False
        }

        lines = [(0, 0, debit_val), (0, 0, credit_val)]
        return lines

    def open_reject_wizard(self, in_relevet, date_rejet):
        # date = fields.Date.context_today(self)
        for pec in self:
            journal_id = pec.journal_id
            bank_acc_account = pec.model_id.at_bank_account.id
            clt_account_id = self.get_partner_account(pec.client, 'client')

            if not in_relevet:
                journal_id = pec.bordereau_id.journal_id
                lines = self.create_accounting_lines(pec, clt_account_id, bank_acc_account)
            else:
                bank_liquidity_acc = self.env.ref('l10n_maroc.1_pcg_51410000').id
                lines_bank = self.create_accounting_lines(pec, bank_liquidity_acc, bank_acc_account)
                lines_clt = self.create_accounting_lines(pec, clt_account_id, bank_liquidity_acc)
                lines = lines_clt + lines_bank

            pec_name = pec.name
            if pec.state == 'at_bank':
                pec_name = pec.name + '[REJ]'

            move = self.env['account.move'].create({
                'journal_id': journal_id.id,
                'date': date_rejet,
                'name': pec_name,
                'ref': pec.note,
                # 'type': 'entry',
                'line_ids': lines,
            })
            move.post()
            lines = pec.move_line_ids.filtered(lambda x: x.account_id.user_type_id.type in ('receivable', 'payable'))
            lines.reconcile()

            pec.write({'state': 'rejected', 'rejete': True})
            pec.payed_date = fields.Date.context_today(self)
        return True

    def action_rejected(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'context': {'pec': self},
            'view_mode': 'form',
            'res_model': 'rejet.pec.wizard',
            'target': 'new',
        }

    def action_to_represent(self):
        for pec in self:
            caisse_centrale_id = self.env['paiement.caisse'].search([('caisse_centrale', '=', True)], limit=1)
            default = {
                'name': pec.name + '[REP]',
                'pec_origin_id': pec.id,
                'paiement_record_id': pec.paiement_record_id.id,
                'caisse_id': caisse_centrale_id.id,
                'bordereau_id': False
            }
            new_pec_id = pec.copy(default=default)
            new_pec_id.action_caisse()
            new_pec_id.action_caisse_centrale()
            pec.write({'state': 'to_represent', 'name': pec.name + '/' + 'Rejete', 'rejete': True})
        res = self.env.ref('account_tres_customer.pec_form_client_view')
        return {
            'name': 'Chèques',
            'view_mode': 'form',
            'view_id': [res and res.id or False],
            'res_model': 'paiement.pec.client',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'nodestroy': True,
            'res_id': new_pec_id.id or False,
        }

    def pec_to_change(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Chèque',
            'view_mode': 'form',
            'res_model': 'pec_to_change',
            'target': 'new',
        }


class PecAssurance(models.Model):
    _name = 'pec.assurance'

    name = fields.Char('Nom')
