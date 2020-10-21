# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

from odoo.tools.translate import _
import math


class AccountAsset(models.Model):
    _inherit = "account.asset.asset"

    product_id = fields.Many2one('product.template', u'Article')
    lot_id = fields.Many2one('stock.production.lot', u'Numéro de serie')
    num_so = fields.Char('N° de BC/')

    asset_stock_inventory = fields.Many2one('stock.location', string="Emplacement d\'immobilisation", compute='_compute_location')
    num_salle = fields.Many2one('stock.location', string="Salle", compute='_compute_location')
    num_ordre = fields.Char(u'Numéro d\'ordre', default='/')
    code_inventaire = fields.Char('Code d\'inventaire', compute='_compute_inventory_code', default='')
    bar_code_print = fields.Char('Code à imprimer', compute='_compute_inventory_code', default='')
    affectataire = fields.Many2one('hr.employee', string='Affectataire')
    account_id = fields.Many2one('account.account', related='product_id.property_account_expense_id', string='Compte Comptable')

    @api.depends('num_ordre', 'product_id.property_account_expense_id', 'num_salle', 'num_ordre')
    def _compute_inventory_code(self):
        for rec in self:
            rec.code_inventaire = ''
            rec.bar_code_print = ''
            if rec.product_id and rec.asset_stock_inventory and rec.num_salle and rec.product_id.property_account_expense_id:
                rec.code_inventaire = rec.product_id.property_account_expense_id.code[
                                      :5] + rec.asset_stock_inventory.name + rec.num_salle.name + rec.num_ordre
                rec.bar_code_print = '1' + rec.num_salle.name + rec.num_ordre
            # else:
            #     raise ValidationError('Merci de paraméter l\'article')

    @api.depends('lot_id')
    def _compute_location(self):
        for rec in self:
            if rec.lot_id:
                quant_id = self.env['stock.quant'].search([('lot_id', '=', rec.lot_id.id)])[-1]
                if quant_id:
                    location = quant_id.location_id
                    rec.num_salle = location
                    if location.location_id:
                        rec.asset_stock_inventory = location.location_id

    @api.model
    def create(self, vals):
        if not vals.get('num_ordre') or vals['num_ordre'] == ('/'):
            vals['num_ordre'] = self.env['ir.sequence'].next_by_code('asset_order_number') or ('/')
        return super(AccountAsset, self).create(vals)

    def action_print(self):
        return self.env.ref('account_asset_extend.report_asset_label_A4_57x35').with_context(discard_logo_check=True).report_action(self.id)



