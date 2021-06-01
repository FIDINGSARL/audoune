# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class PaiementChequeClient(models.Model):
    _inherit = 'paiement.cheque.client'

    engagement_id = fields.Binary('Engagement')
    in_name_of_id = fields.Many2one('res.partner', 'Au nom de')
    pc_id = fields.Binary('Photocopie du chèque')
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]},
                                 default=lambda self: self.env.ref('account_tres_customer.account_journal_data_chp'))
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]},
                       default=fields.date.today())
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse', default=lambda self: self.env.user.caisse_id)
    model_id = fields.Many2one('paiement.pec.model.client', string=u'Modèle Comptable',
                               required=True, states={'payed': [('readonly', True)]},
                               default=lambda self: self.env.ref('account_tres_customer.paiement_cheque_model_client1'))
    due_date = fields.Date(string=u"Date d'échéance", required=True, states={'payed': [('readonly', True)]},
                           default=fields.date.today())
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
                summary='Champs à renseigner pour le chèque du numéro ' + vals[
                    'name'] + ' du patient ' + client_id.name,
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

    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]},
                                 default=lambda self: self.env['account.journal'].search([('name', 'like', 'Esp%')]))
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse', default=lambda self: self.env.user.caisse_id)
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]},
                       default=fields.date.today())


class SupplierPaymentCash(models.Model):
    _inherit = "paiement.cash.supplier"

    name = fields.Char(string=u'Numéro', readonly=True, required=False)
    patient_id = fields.Many2one('res.partner', string="Patient")
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]},
                                 default=lambda self: self.env['account.journal'].search([('name', 'like', 'Esp%')]))
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]},
                       default=fields.date.today())
    period_id = fields.Many2one('date.range', string=u'Période', required=False)
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse', default=lambda self: self.env.user.caisse_id)

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_extend.seq_tres_supplier_cash').next_by_code(
            'paiement.cash.supplier') or ''
        res = super(SupplierPaymentCash, self).create(vals)
        return res


class SupplierPaymentEffet(models.Model):
    _inherit = "paiement.effet.supplier"

    name = fields.Char(string=u'Numéro', readonly=True, required=False)

    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]},
                                 default=lambda self: self.env['account.journal'].search([('name', 'like', 'Esp%')]))
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]},
                       default=fields.date.today())
    period_id = fields.Many2one('date.range', string=u'Période', required=False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_extend.seq_tres_supplier_effet').next_by_code(
            'paiement.effet.supplier') or ''
        res = super(SupplierPaymentEffet, self).create(vals)
        return res


class SupplierPaymentOv(models.Model):
    _inherit = "paiement.ov.supplier"

    name = fields.Char(string=u'Numéro', readonly=True, required=False)

    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]},
                                 default=lambda self: self.env['account.journal'].search([('name', 'like', 'Esp%')]))
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]},
                       default=fields.date.today())
    period_id = fields.Many2one('date.range', string=u'Période', required=False)

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_extend.seq_tres_supplier_effet').next_by_code(
            'paiement.effet.supplier') or ''
        res = super(SupplierPaymentOv, self).create(vals)
        return res


class SupplierPaymentCheque(models.Model):
    _inherit = "paiement.cheque.supplier"

    name = fields.Char(string=u'Numéro', readonly=True, required=False)
    journal_id = fields.Many2one('account.journal', string=u'Journal', states={'payed': [('readonly', True)]},
                                 default=lambda self: self.env['account.journal'].search([('name', 'like', 'Esp%')]))
    date = fields.Date(string="Date", required=True, states={'payed': [('readonly', True)]},
                       default=fields.date.today())
    period_id = fields.Many2one('date.range', string=u'Période', required=False)
    caisse_id = fields.Many2one('paiement.caisse', string=u'Caisse', default=lambda self: self.env.user.caisse_id)

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('account_tres_extend.seq_tres_supplier_cheque').next_by_code(
            'paiement.cheque.supplier') or ''
        res = super(SupplierPaymentCheque, self).create(vals)
        return res


class PaiementCaisse(models.Model):
    _inherit = 'paiement.caisse'

    @api.depends('cheque_lines', 'effet_lines', 'ov_lines', 'pec_lines', 'cash_lines.amount')
    def _calc_total_amount(self):
        for rec in self:
            rec.nb_cheques = len(rec.cheque_lines)
            rec.nb_effets = len(rec.effet_lines)
            rec.nb_ov = len(rec.ov_lines)
            rec.nb_cb = len(rec.cb_lines)
            rec.nb_pec = len(rec.pec_lines)
            rec.nb_cheque_supplier = len(rec.supplier_cheque_lines)
            rec.nb_cash_supplier = len(rec.supplier_cash_lines)
            rec.total_cash = sum(cash.amount for cash in rec.cash_lines)
            rec.total_amount = sum(cheque.amount for cheque in rec.cheque_lines) + sum(
                effet.amount for effet in rec.effet_lines) + \
                               sum(ov.amount for ov in rec.ov_lines) + sum(
                cash.amount for cash in rec.cash_lines) + sum(cb.amount for cb in rec.cb_lines) \
                               + sum(cb.amount for cb in rec.pec_lines) - sum(
                schk.amount for schk in rec.supplier_cheque_lines) \
                               - sum(scash.amount for scash in rec.supplier_cash_lines)

    supplier_cheque_lines = fields.One2many('paiement.cheque.supplier', 'caisse_id', string=u'Chèques Fournisseur',
                                            readonly=True)
    supplier_cash_lines = fields.One2many('paiement.cash.supplier', 'caisse_id', string=u'Cash Fournisseur',
                                          readonly=True)
    nb_cheque_supplier = fields.Float(compute='_calc_total_amount', string=u"Nombre de chèques fournisseur")
    nb_cash_supplier = fields.Float(compute='_calc_total_amount', string=u"Nombre de cash fournisseur")
    total_cash = fields.Float('Total Éspèce', compute='_calc_total_amount')