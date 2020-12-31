# -*- encoding: utf-8 -*-

from odoo import models,fields, api
from odoo.exceptions import ValidationError


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    partner_id = fields.Many2one('res.partner', 'Client')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    partner_id = fields.Many2one('res.partner', related="lot_producing_id.partner_id", string='Client', store=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _lots_count(self):
        for rec in self:
            rec.count_lots_client = len(rec.lot_client_ids)

    count_lots_client = fields.Integer(compute='_lots_count', string=u'Nbre de numéros de séries')
    lot_client_ids = fields.One2many('mrp.production', 'partner_id', string=u'Numéros de séries', readonly=True)


