# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class PaiementChequeClient(models.Model):
    _inherit = "paiement.pec.client"

    bordereau_id = fields.Many2one('paiement.bordereau', 'Bordereau')


class PaiementBordereau(models.Model):
    _inherit = 'paiement.bordereau'

    @api.depends('cheque_lines', 'effet_lines', 'pec_lines')
    def _calc_total_amount(self):
        self.total_amount_ok = sum(cheque.amount for cheque in self.cheque_lines if cheque.state == 'payed') + sum(effet.amount for effet in self.effet_lines if effet.state == 'payed') + sum(pec.amount for pec in self.pec_lines if pec.state == 'payed')
        self.total_amount_ko = sum(cheque.amount for cheque in self.cheque_lines if cheque.state not in ['payed', 'rejected']) + sum(effet.amount for effet in self.effet_lines if effet.state not in ['payed', 'rejected']) + sum(pec.amount for pec in self.pec_lines if pec.state not in ['payed', 'rejected'])
        self.total_amount_rejet = sum(cheque.amount for cheque in self.cheque_lines if cheque.state == 'rejected') + sum(effet.amount for effet in self.effet_lines if effet.state == 'rejected') + sum(pec.amount for pec in self.pec_lines if pec.state == 'rejected')
        self.nb_cheques = len(self.cheque_lines)
        self.nb_effets = len(self.effet_lines)
        self.nb_pec = len(self.pec_lines)
        self.total_amount = sum(self.cheque_lines.mapped('amount'))+ sum(self.effet_lines.mapped('amount')) + sum(self.pec_lines.mapped('amount'))

    pec_lines = fields.One2many('paiement.pec.client', 'bordereau_id', string=u'Prises en charges', copy=False)
    nb_pec = fields.Integer(compute='_calc_total_amount', string=u'Nombre de prises en charge')

    def valider_bordereau(self):
        for record in self:
            for ch in record.cheque_lines:
                if ch.state == 'caisse':
                    ch.action_caisse_centrale()
                    ch.action_received()
                if ch.state == 'caisse_centrale':
                    ch.action_received()
                # ch.write({'caisse_id': False, 'journal_id': record.journal_id.id})
                ch.write({'caisse_id': False, 'journal_id': ch.journal_id.id})
            for ef in record.effet_lines:
                if ef.state == 'caisse':
                    ef.action_caisse_centrale()
                    ef.action_received()
                if ef.state == 'caisse_centrale':
                    ef.action_received()
                ef.action_received()
            for pec in record.pec_lines:
                if pec.state == 'caisse':
                    pec.action_caisse_centrale()
                    pec.action_received()
                if pec.state == 'caisse_centrale':
                    pec.action_received()
                pec.action_received()
                # ef.write({'caisse_id': False, 'journal_id': record.journal_id.id})
                pec.write({'caisse_id': False, 'journal_id': pec.journal_id.id})
            record.write({'state': 'done'})
        return True

    def rec_bordereau(self):
        attach_obj = self.env['ir.attachment']
        for record in self:
            has_attachment = self.env['ir.config_parameter'].sudo().get_param('account_tres_customer.has_attachment')
            if has_attachment:
                attachment_ids = attach_obj.search(
                    [('res_model', '=', 'paiement.bordereau'), ('res_id', '=', record.id)])
                if not attachment_ids:
                    raise UserError(u'Vous devez attacher le bordereau scanné')
            for ch in record.cheque_lines:
                if ch.state == 'received':
                    ch.action_at_bank()
            for ef in record.effet_lines:
                if ef.state == 'received':
                    ef.action_at_bank()
            for pec in record.pec_lines:
                if pec.state == 'received':
                    pec.action_at_bank()
            record.write({'state': 'received'})
        return True

    def action_post_fees(self):
        for record in self:
            for fees in record.tres_fees_ids:
                if fees.state == 'draft':
                    fees.create_account_lines()

    def back_to_draft(self):
        for record in self:
            move_ids = []
            for l in record.effet_lines:
                for mv in l.move_line_ids:
                    mv.move_id.button_cancel()
                    move_ids.append(mv.move_id.id)
                l.move_line_ids.unlink()
                l.write({'state': 'draft'})
                l.action_caisse()
            for l in record.cheque_lines:
                for mv in l.move_line_ids:
                    mv.move_id.button_cancel()
                    move_ids.append(mv.move_id.id)
                l.move_line_ids.unlink()
                l.write({'state': 'draft'})
                l.action_caisse()
            for l in record.pec_lines:
                for mv in l.move_line_ids:
                    mv.move_id.button_cancel()
                    move_ids.append(mv.move_id.id)
                l.move_line_ids.unlink()
                l.write({'state': 'draft'})
                l.action_caisse()
            self.env['account.move'].browse(move_ids).unlink()
            record.write({'state': 'draft'})
        return True

    # @api.model
    # def default_get(self, fields):
    #     res = super(PaiementBordereau, self).default_get(fields)
    #     res['name'] = '/'
    #     return res
    #
    # @api.model
    # def create(self, vals):
    #     if vals['name'] == '/' or not vals['name']:
    #         vals['name'] = self.env['ir.sequence'].next_by_code('paiement.bordereau')
    #     return super(PaiementBordereau, self).create(vals)
    #
    # def copy(self, default=None):
    #     if not default:
    #         default = {}
    #     default.update({
    #         'state': 'draft',
    #         'name':  self.env['ir.sequence'].next_by_code('paiement.bordereau')
    #     })
    #     return super(PaiementBordereau, self).copy(default)
