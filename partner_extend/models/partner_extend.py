# -*- encoding: utf-8 -*-

from odoo import models,fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    id_fisc = fields.Char(string=u'Identifiant Fiscal')
    rc = fields.Char(string=u'RC')
    cnss = fields.Char(string=u'Numéro de la sécurité sociale')
    capital_social = fields.Char(string=u'Capital social')
    ice = fields.Char(string=u'ICE')
    itp = fields.Char(string=u'Identifiant Taxe Professionnelle')
    activites = fields.Char(string=u"Profession ou activités exercées")
    nationalite = fields.Char(string=u"Nationalité")
    fax = fields.Char(string=u"Fax")
    assurance1 = fields.Many2one('pec.assurance', string=u"Assurance 1")
    assurance2 = fields.Many2one('pec.assurance', string=u"Assurance 2")
    cin = fields.Char(string=u'CIN')
    authorized_company_ids = fields.Many2many('res.company', string="Sociétés Autorisées")
    company_creating_id = fields.Many2one('res.company', string="Société Responsable du client", default=lambda self: self.env.company, readonly=True)
    is_partner_visible = fields.Boolean('Est visible ?', default=False, compute='_compute_partner_visibility')
    is_authorized_company_ids_editable = fields.Boolean('Est modifiable ?', default=False, compute='_compute_partner_visibility')

    @api.constrains('ice')
    def _check_ice(self):
        for rec in self:
            if rec.ice and (len(rec.ice) != 15 or not rec.ice.isdigit()):
                    raise ValidationError(u"L'ICE doit être constitué de 15 chiffres")

    @api.depends('company_creating_id', 'authorized_company_ids')
    def _compute_partner_visibility(self):
        for rec in self:
            if self.env.company.id in rec.authorized_company_ids.mapped('id') \
                    or self.env.company.id == rec.company_creating_id.id\
                    or rec.id == self.env.user.partner_id.id\
                    or rec.id == self.env.ref('base.partner_root').id:  # Odoo Bot
                rec.is_partner_visible = True
            else:
                rec.is_partner_visible = False

            if self.env.company.id == rec.company_creating_id.id:
                rec.is_authorized_company_ids_editable = True
            else:
                rec.is_authorized_company_ids_editable = False



