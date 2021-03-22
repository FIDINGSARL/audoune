# -*- encoding: utf-8 -*-

from odoo import models,fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_dp = fields.Boolean(string='Est un dossier physique')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_dp = fields.Boolean(related="product_tmpl_id.is_dp", string='Est un dossier physique')


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    partner_id = fields.Many2one('res.partner', 'Client')
    available_qty = fields.Float('Quantité disponible', compute='_compute_available_qty')
    is_dp = fields.Boolean(related='product_id.is_dp', string='Est un dossier physique')
    # is_admin = fields.Boolean('Est un admin', compute='_is_admin')
    is_admin = fields.Boolean('Est un admin', default=lambda self: self.env.user.has_group('base.group_system'))

    def _is_admin(self):
        for rec in self:
            rec.is_admin = self.env.user.has_group('base.group_system')

    def _compute_available_qty(self):
        for rec in self:
            rec.available_qty = 0
            if self._context.get('location_id', False):
                location_id = self.env['stock.warehouse'].browse(self._context['location_id'])
                stock_quant = self.env['stock.quant'].search([
                        ('location_id', '=', location_id.lot_stock_id.id),
                        ('lot_id', '=', rec.id),
                    ])
                rec.available_qty = stock_quant.available_quantity


class MrpProduction(models.Model):
    _inherit = 'stock.production.lot'

    partner_id = fields.Many2one('res.partner', string='Client', store=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _lots_count(self):
        for rec in self:
            rec.count_lots_client = len(rec.lot_client_ids.filtered(lambda serial: serial.is_dp is True))

    count_lots_client = fields.Integer(compute='_lots_count', string=u'Nbre de dossier physiques')
    lot_client_ids = fields.One2many('stock.production.lot', 'partner_id', string=u'Dossiers Physiques', readonly=True)


