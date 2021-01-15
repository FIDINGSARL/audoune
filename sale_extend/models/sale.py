# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    tag_ids = fields.Many2many('crm.tag', related="order_id.tag_ids", string='Étiquettes')
    lot_id = fields.Many2one('stock.production.lot', 'Numéro de série')

    def write(self, vals):
        if vals.get('lot_id', False):
            lot_id = self.env['stock.production.lot'].browse(vals['lot_id'])
            existing_line = self.env['sale.order.line'].search([]).filtered(lambda line: line.lot_id == lot_id)
            if not existing_line:
                lot_id.write({
                    'partner_id': self.order_id.partner_id.id
                })
            else:
                raise ValidationError('Ce numéro de série est déjà affécté')
        return super(SaleOrderLine, self).write(vals)
