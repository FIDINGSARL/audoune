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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cons_purchase_id = fields.Many2one('purchase.order', string="Achat de le consultation")
    cons_invoice_id = fields.Many2one('account.move', string="Facture de le consultation")
    is_cons_purchase = fields.Boolean('Achat relatif à une consultation', default=False)

    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     if not self.is_cons_purchase:
    #         dr_obj = self.env['dossier.rembourssement']
    #         for assurance in self.partner_id.assurance_ids:
    #             dr_obj.create({
    #                 'partner_id': self.partner_id.id,
    #                 'date': fields.Date.today(),
    #                 'assurance_id': assurance.assurance_id.id,
    #                 'amount': 0.0
    #             })
    #
    #         dr_obj.create({
    #             'partner_id': self.partner_id.id,
    #             'date': fields.Date.today(),
    #             'assurance_id': False,
    #             'amount': 0.0
    #         })
    #     return res

