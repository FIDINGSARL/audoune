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
            res.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Champs à renseigner pour la fiche du patient ' + vals['name'],
                note="<ul class='o_checklist'>" +
                     ' '.join(missing)
                     + "</ul>",
                user_id=self.env.user.id)
        return res


class PartnerAssurance(models.Model):
    _name = 'partner.assurance'

    assurance_id = fields.Many2one('pec.assurance', 'Assurance')
    partner_id = fields.Many2one('res.partner', 'Patient')
    num_affi = fields.Char('Numéro d\'affiliation')
    num_imma = fields.Char('Numéro d\'immatriculation')
    num_fonda = fields.Char('Numéro de la fondation')
