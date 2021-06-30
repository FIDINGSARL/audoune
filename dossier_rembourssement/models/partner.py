# -*- encoding: utf-8 -*-

from odoo import models,fields, api


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _dr_count(self):
        for partner in self:
            count_dr_client = len(partner.dr_client_ids)
            partner.count_dr_client = count_dr_client

    count_dr_client = fields.Integer(compute='_dr_count', string=u'Nbre des dr')
    dr_client_ids = fields.One2many('dossier.rembourssement', 'partner_id', string=u'Dossiers de rembourssement')
