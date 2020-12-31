# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    tag_ids = fields.Many2many('crm.tag', related="order_id.tag_ids", string='Étiquettes')
