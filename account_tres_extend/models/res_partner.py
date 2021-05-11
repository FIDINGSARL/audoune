# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _cons_count(self):
        for rec in self:
            rec.count_cons_client = len(rec.cons_client_ids)

    count_cons_client = fields.Integer(compute='_cons_count', string=u'Nbre de consultations achetées')
    cons_client_ids = fields.One2many('paiement.cash.supplier', 'patient_id', string=u'Consultations achetées', readonly=True)
