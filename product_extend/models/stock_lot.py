# -*- encoding: utf-8 -*-

from odoo import models,fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_dp = fields.Boolean(string='Est un dossier physique')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_dp = fields.Boolean(string='Est un dossier physique')


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    partner_id = fields.Many2one('res.partner', 'Client')
    available_qty = fields.Float('Quantité disponible', compute='_compute_available_qty', store=True)
    is_dp = fields.Boolean(related='product_id.is_dp', string='Est un dossier physique')
    # is_admin = fields.Boolean('Est un admin', compute='_is_admin')
    is_admin = fields.Boolean('Est un admin', compute='_is_admin')

    @api.onchange('is_dp')
    def on_change_dp(self):
        if self.is_dp:
            self.note = "<ul class='o_checklist'> " \
                        "<li id='checklist-id-1'><p>Mutuelle</p></li>" \
                        "<li id='checklist-id-2'><p>Certificat médical</p></li>" \
                        "<li id='checklist-id-3'><p>Prescription</p></li>" \
                        "<li id='checklist-id-4'><p>Audiogramme</p></li>" \
                        "<li id='checklist-id-5'><p>Audiométrie vocale</p></li>" \
                        "</ul>"
        else:
            self.note = ""

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
    _inherit = 'mrp.production'

    partner_id = fields.Many2one('res.partner', string='Client', required=True)

    def action_generate_serial(self):
        self.ensure_one()
        self.lot_producing_id = self.env['stock.production.lot'].create({
            'product_id': self.product_id.id,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id
        })
        if self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_line_ids:
            self.move_finished_ids.filtered(lambda m: m.product_id == self.product_id).move_line_ids.lot_id = self.lot_producing_id
        if self.product_id.tracking == 'serial':
            self._set_qty_producing()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _lots_count(self):
        for rec in self:
            rec.count_lots_client = len(rec.lot_client_ids)
            rec.count_prod_client = len(rec.prod_client_ids)

    count_lots_client = fields.Integer(compute='_lots_count', string=u'Nbre de numéros de séries')
    count_prod_client = fields.Integer(compute='_lots_count', string=u'Nbre de productions')
    lot_client_ids = fields.One2many('stock.production.lot', 'partner_id', string=u'Numéros de séries', readonly=True)
    prod_client_ids = fields.One2many('mrp.production', 'partner_id', string=u'Productions', readonly=True)


