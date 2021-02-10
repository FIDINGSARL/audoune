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
    assurance1 = fields.Many2one('pec.assurance', string=u"Assurance 1")
    assurance2 = fields.Many2one('pec.assurance', string=u"Assurance 2")
    cin = fields.Char(string=u'CIN')
    see_all = fields.Boolean('Visible par tout le monde', default=False)
    user_id = fields.Many2one(default=lambda self: self.env.user.id)
    # authorized_company_ids = fields.Many2many('res.company', string="Sociétés Autorisées")
    # company_creating_id = fields.Many2one('res.company', string="Société Responsable du client", default=lambda self: self.env.company, readonly=True)
    # is_partner_visible = fields.Boolean('Est visible ?', default=False, compute='_compute_partner_visibility')
    is_editable = fields.Boolean('Est modifiable ?', default=False, compute='_compute_partner_visibility')

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
