# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
        if not vals.get('autres', False):
            missing.append("<li id='checklist-id-3'><p>autres</p></li>")

        if vals.get('assurance_ids', False):
            for line in vals['assurance_ids']:
                assurance_id = self.env['pec.assurance'].browse(line[2]['assurance_id'])
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
            missing.append("<li id='checklist-id-3'><p>La liste des assurances du patient " + vals['name'] + "</p></li>")

        res = super(ResPartner, self).create(vals)
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
    cons_client_ids = fields.One2many('account.move.line', 'patient_id', string=u'Consultations achetées', readonly=True)


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
