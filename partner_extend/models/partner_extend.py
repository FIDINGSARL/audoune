# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang


class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'), ('company', 'Company')],
                                    default='person',
                                    compute='_compute_company_type', inverse='_write_company_type')

    id_fisc = fields.Char(string=u'Identifiant Fiscal')
    rc = fields.Char(string=u'RC')
    cnss = fields.Char(string=u'Numéro de la sécurité sociale')
    capital_social = fields.Char(string=u'Capital social')
    ice = fields.Char(string=u'ICE')
    itp = fields.Char(string=u'Identifiant Taxe Professionnelle')
    activites = fields.Char(string=u"Profession ou activités exercées")
    nationalite = fields.Char(string=u"Nationalité")
    fax = fields.Char(string=u"Fax")
    assurance_ids = fields.One2many('partner.assurance', 'partner_id', string=u"Assurances")
    see_all = fields.Boolean('Visible par tout le monde', default=False)
    user_id = fields.Many2one(default=lambda self: self.env.user.id)
    is_editable = fields.Boolean('Est modifiable ?', default=False, compute='_compute_partner_visibility')
    cin = fields.Char(string=u'CIN')
    password = fields.Char(string=u'Mot de passe')
    cin_attachment_id = fields.Binary('Photocopie CIN')
    mut_attachment_id = fields.Binary('Photocopie Mutuelle')
    comp_attachment_id = fields.Binary('Photocopie Complémentaire')
    delapartun_id = fields.Many2one('res.partner', 'De la part un')
    plateforme = fields.Many2one('utm.medium', 'Plateforme')
    delapartdeux_id = fields.Many2one('res.partner', 'De la part deux')
    is_autres = fields.Boolean('Autres')
    autres = fields.Many2one('utm.medium', 'Autres')
    medecin_id = fields.Many2one('res.partner', string='Médecin')
    state = fields.Selection([('non_valid', 'Non validé'),
                              ('valid', u'Validé')], 'Etat', default='non_valid', readonly=True, required=True)

    def client_to_valid(self):
        if self.count_cheque_client == 0 and self.count_cash_client == 0:
            raise ValidationError('Le client ne peut pas être validé sans donner d\'avance')
        if self.opportunity_ids:
            opportunity_id = self.opportunity_ids[0]
            opportunity_id.write({
                'stage_id': self.env.ref('crm.stage_lead4').id
            })
        self.write({
            'state': 'valid'
        })

    def client_to_non_valid(self):
        self.write({
            'state': 'non_valid'
        })

    def update_crm_partner_extend(self):
        recs = self.env['res.partner'].search([])
        for rec in recs:
            if rec.state == 'non_valid':
                if rec.opportunity_ids:
                    print('inside', rec.opportunity_ids)
                    if rec.opportunity_ids[0].stage_id in [self.env.ref('crm_extend.lead_stage_centre'), self.env.ref('crm_extend.lead_stage_non_arrive')]:
                        rec.opportunity_ids[0].write({
                            'stage_id': self.env.ref('crm_extend.lead_stage_relance').id
                        })

    @api.constrains('ice')
    def _check_ice(self):
        for rec in self:
            if rec.ice and (len(rec.ice) != 15 or not rec.ice.isdigit()):
                raise ValidationError(u"L'ICE doit être constitué de 15 chiffres")

    @api.depends('user_id')
    def _compute_partner_visibility(self):
        self = self.sudo()
        for rec in self:
            if self.env.user.id == rec.user_id.id or self.env.user.id == self.env.ref('base.user_admin').id:
                rec.is_editable = True
            else:
                rec.is_editable = False

    @api.model
    def create(self, vals):
        missing = []
        dr_obj = self.env['dossier.rembourssement']
        missing.append("<li id='checklist-id-1'><p>Dossier Physique</p></li>")
        if not vals.get('phone', False):
            missing.append("<li id='checklist-id-1'><p>Numéro de Téléphone</p></li>")
        if not vals.get('cin', False):
            missing.append("<li id='checklist-id-1'><p>Numéro de CIN</p></li>")
        if not vals.get('password', False):
            missing.append("<li id='checklist-id-1'><p>Mot de passe</p></li>")
        if not vals.get('cin_attachment_id', False):
            missing.append("<li id='checklist-id-1'><p>Photocopie CIN</p></li>")
        if not vals.get('mut_attachment_id', False):
            missing.append("<li id='checklist-id-2'><p>Photocopie Mutuelle</p></li>")
        if not vals.get('comp_attachment_id', False):
            missing.append("<li id='checklist-id-3'><p>Photocopie Complémentaire</p></li>")
        if not vals.get('delapartun_id', False):
            missing.append("<li id='checklist-id-3'><p>De la part un</p></li>")
        if not vals.get('plateforme', False):
            missing.append("<li id='checklist-id-3'><p>Plateforme</p></li>")
        if not vals.get('delapartdeux_id', False):
            missing.append("<li id='checklist-id-3'><p>De la part deux</p></li>")

        res = super(ResPartner, self).create(vals)
        print('res', res)
        dr_obj.create({
            'partner_id': res.id,
            'date': fields.Date.today(),
            'assurance_id': False,
            'amount': 0.0
        })
        if vals.get('assurance_ids', False):
            for line in vals['assurance_ids']:
                assurance_id = self.env['pec.assurance'].browse(line[2]['assurance_id'])
                dr_obj.create({
                    'partner_id': res.id,
                    'date': fields.Date.today(),
                    'assurance_id': assurance_id.id,
                    'amount': 0.0
                })
                if not line[2]['num_affi']:
                    missing.append("<li id='checklist-id-3'><p>Numéro d'affiliation relatif à l'assurance "
                                   + assurance_id.name + "</p></li>")
                if not line[2]['num_imma']:
                    missing.append("<li id='checklist-id-3'><p>Numéro d'immatriculation relatif à l'assurance "
                                   + assurance_id.name + "</p></li>")
                if not line[2]['num_fonda']:
                    missing.append("<li id='checklist-id-3'><p>Numéro de la fondation relatif à l'assurance "
                                   + assurance_id.name + "</p></li>")
        else:
            missing.append(
                "<li id='checklist-id-3'><p>La liste des assurances du patient " + vals['name'] + "</p></li>")

        if missing:
            # res.activity_schedule(
            #     activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
            #     summary='Champs à renseigner pour la fiche du patient ' + vals['name'],
            #     note="<ul class='o_checklist'>" +
            #          ' '.join(missing)
            #          + "</ul>",
            #     user_id=self.env.user.id)
            activity_id = self.env['mail.activity'].with_user(self.env.ref('base.user_admin')).create({
                'summary': 'Champs à renseigner pour la fiche du patient ' + vals['name'],
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_model_id': self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1).id,
                'note': "<ul class='o_checklist'>" +
                        ' '.join(missing)
                        + "</ul>",
                'res_id': res.id,
                'user_id': self.env.user.id
            })
        return res

    def creer_consultation(self):
        if not self.medecin_id:
            raise ValidationError('Veuillez renseigner le médecin pour pouvoir créer la consultation')
        sale_order_obj = self.env['sale.order']
        purchase_order_obj = self.env['purchase.order']
        invoice_obj = self.env['account.move']
        consultation_product_id = self.env.ref('product_extend.product_product_consultation')
        nblk_journal_id = self.env.ref('journal_nblk.account_journal_data_nblk')
        sale_order_line = (0, 0, {
            'product_id': consultation_product_id.id,
            'product_uom_qty': 1,
        })
        purchase_order_line = (0, 0, {
            'product_id': consultation_product_id.id,
            'product_qty': 1,
            'price_unit': consultation_product_id.standard_price,
        })
        invoice_line = (0, 0, {
            'product_id': consultation_product_id.id,
            'quantity': 1,
            'price_unit': consultation_product_id.list_price,
        })
        purchase_id = purchase_order_obj.create({
            'partner_id': self.medecin_id.id,
            'order_line': [purchase_order_line]
        })
        purchase_id.button_confirm()
        invoice_id = invoice_obj.create({
            'partner_id': self.id,
            'invoice_line_ids': [invoice_line],
            'move_type': 'out_invoice',
            'journal_id': nblk_journal_id.id
        })
        invoice_id.action_post()
        sale_order_id = sale_order_obj.create({
            'partner_id': self.id,
            'order_line': [sale_order_line],
            'cons_purchase_id': purchase_id.id,
            'cons_invoice_id': invoice_id.id,
            'is_cons_purchase': True
        })
        sale_order_id.action_confirm()

    def _compute_for_followup(self):
        """
        Compute the fields 'total_due', 'total_overdue','followup_level' and 'followup_status'
        """
        first_followup_level = self.env['account_followup.followup.line'].search([('company_id', '=', self.env.company.id)], order="delay asc", limit=1)
        followup_data = self._query_followup_level()
        today = fields.Date.context_today(self)
        for record in self:
            total_due = 0
            total_overdue = 0
            followup_status = "no_action_needed"
            for aml in record.unreconciled_aml_ids:
                print('aml.cheque_client_id', aml.cheque_client_id)
                if aml.cheque_client_id and not aml.cheque_client_id.accord:
                    continue
                if aml.company_id == self.env.company:
                    amount = aml.amount_residual
                    total_due += amount
                    is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                    if is_overdue and not aml.blocked:
                        total_overdue += amount
            record.total_due = total_due
            print('record.total_due', record.total_due)
            record.total_overdue = total_overdue
            if record.id in followup_data:
                record.followup_status = followup_data[record.id]['followup_status']
                record.followup_level = self.env['account_followup.followup.line'].browse(followup_data[record.id]['followup_level']) or first_followup_level
            else:
                record.followup_status = 'no_action_needed'
                record.followup_level = first_followup_level

    # def _compute_for_followup(self):
    #     """
    #     Compute the fields 'total_due', 'total_overdue','followup_level' and 'followup_status'
    #     """
    #     first_followup_level = self.env['account_followup.followup.line'].search(
    #         [('company_id', '=', self.env.company.id)], order="delay asc", limit=1)
    #     followup_data = self._query_followup_level()
    #     today = fields.Date.context_today(self)
    #     for record in self:
    #         total_due = 0
    #         total_overdue = 0
    #         followup_status = "no_action_needed"
    #         for aml in record.unreconciled_aml_ids:
    #             if aml.company_id == self.env.company:
    #                 amount = aml.amount_residual
    #                 if not aml.move_id.journal_id.code == 'NBL':
    #                     total_due += amount
    #                     is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
    #                     if is_overdue and not aml.blocked:
    #                         total_overdue += amount
    #         record.total_due = total_due
    #         record.total_overdue = total_overdue
    #         if record.id in followup_data:
    #             record.followup_status = followup_data[record.id]['followup_status']
    #             record.followup_level = self.env['account_followup.followup.line'].browse(
    #                 followup_data[record.id]['followup_level']) or first_followup_level
    #         else:
    #             record.followup_status = 'no_action_needed'
    #             record.followup_level = first_followup_level
    #
    # def _invoice_total(self):
    #     self.total_invoiced = 0
    #     if not self.ids:
    #         return True
    #
    #     all_partners_and_children = {}
    #     all_partner_ids = []
    #     for partner in self.filtered('id'):
    #         # price_total is in the company currency
    #         all_partners_and_children[partner] = self.with_context(active_test=False).search(
    #             [('id', 'child_of', partner.id)]).ids
    #         all_partner_ids += all_partners_and_children[partner]
    #
    #     domain = [
    #         ('partner_id', 'in', all_partner_ids),
    #         ('state', 'not in', ['draft', 'cancel']),
    #         ('move_type', 'in', ('out_invoice', 'out_refund')),
    #         ('journal_id.code', '!=', 'NBL'),
    #     ]
    #     price_totals = self.env['account.invoice.report'].read_group(domain, ['price_subtotal'], ['partner_id'])
    #     for partner, child_ids in all_partners_and_children.items():
    #         partner.total_invoiced = sum(
    #             price['price_subtotal'] for price in price_totals if price['partner_id'][0] in child_ids)

    def _cons_count(self):
        for rec in self:
            rec.count_cons_client = len(rec.cons_client_ids)

    count_cons_client = fields.Integer(compute='_cons_count', string=u'Nbre de consultations achetées')
    cons_client_ids = fields.One2many('account.move.line', 'patient_id', string=u'Consultations achetées',
                                      readonly=True)


class PartnerAssurance(models.Model):
    _name = 'partner.assurance'

    assurance_id = fields.Many2one('pec.assurance', 'Assurance', required=1)
    partner_id = fields.Many2one('res.partner', 'Patient')
    num_affi = fields.Char('Numéro d\'affiliation')
    num_imma = fields.Char('Numéro d\'immatriculation')
    num_fonda = fields.Char('Numéro de la fondation')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    patient_id = fields.Many2one('res.partner', string="Patient")
    show_info = fields.Boolean('Montrer onglet infos', compute='_compute_show_info')
    payment_state = fields.Selection(related='move_id.payment_state', string='État de paiement')

    def _compute_show_info(self):
        for rec in self:
            rec.show_info = True
            if self._context.get('default_patient_id', False):
                rec.show_info = False

    @api.constrains('patient_id')
    def _check_ice(self):
        for rec in self:
            exists = self.env['account.move.line'].search([
                ('patient_id', '=', rec.patient_id.id),
                ('id', '!=', rec.id),
                ('move_id.move_type', '=', 'in_invoice'),
            ])
            if exists and rec.patient_id:
                raise ValidationError("Un patient ne peux pas avoir plus que deux consultations")


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_lines(self, options, line_id=None):
        """
        Override
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []

        lang_code = partner.lang if self._context.get('print_mode') else self.env.user.lang or get_lang(self.env).code
        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.company):
            if l.company_id == self.env.company:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                if aml.cheque_client_id and not aml.cheque_client_id.accord:
                    continue
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date', 'style': 'white-space:nowrap;text-align:center;color: red;'}
                if is_payment:
                    date_due = ''
                move_line_name = self._format_aml_name(aml.name, aml.move_id.ref, aml.move_id.name)
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1
                expected_pay_date = format_date(self.env, aml.expected_pay_date, lang_code=lang_code) if aml.expected_pay_date else ''
                invoice_origin = aml.move_id.invoice_origin or ''
                if len(invoice_origin) > 43:
                    invoice_origin = invoice_origin[:40] + '...'
                columns = [
                    format_date(self.env, aml.date, lang_code=lang_code),
                    date_due,
                    invoice_origin,
                    move_line_name,
                    (expected_pay_date and expected_pay_date + ' ') + (aml.internal_note or ''),
                    {'name': '', 'blocked': aml.blocked},
                    amount,
                ]
                if self.env.context.get('print_mode'):
                    columns = columns[:4] + columns[6:]
                lines.append({
                    'id': aml.id,
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'style': 'border-top-style: double',
                'unfoldable': False,
                'level': 3,
                'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [total >= 0 and _('Total Due') or '', total_due]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 3,
                    'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [_('Total Overdue'), total_issued]],
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'style': 'border-bottom-style: none',
                'unfoldable': False,
                'level': 0,
                'columns': [{} for col in columns],
            })
        # Remove the last empty line
        if lines:
            lines.pop()
        return lines
