# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.tools import formataddr

from datetime import datetime, timedelta

from odoo.exceptions import ValidationError


class StockMoveline(models.Model):
    _inherit = 'stock.inventory'

    colis_id = fields.Many2one('stock.colis', 'Colis d\'origine')


class PaiementChequeClient(models.Model):
    _inherit = 'paiement.cheque.client'

    colis_id = fields.Many2one('stock.colis', 'Colis d\'origine')


class StockColis(models.Model):
    _name = "stock.colis"
    _order = 'create_date desc'

    name = fields.Char('Référence', readonly=1)
    state = fields.Selection([('new', 'Nouveau'), ('open', 'Envoyé au Centre'),
                              ('valid', 'Validé par le centre')], string=u'État', required=True,
                             copy=False, default='new')
    divers = fields.Text('Divers')
    user_id = fields.Many2one('res.users', string='Emetteur', default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    is_destinataire = fields.Boolean('Est un destinataire', compute='_compute_is_destinataire')
    company_dest_id = fields.Many2one('res.company', string='Société de destination')
    dossier_physique = fields.Many2many('ir.attachment')
    empreinte_lot_ids = fields.Many2many('stock.production.lot', 'stock_colis_empreinte_lot_rel', 'lot_id')
    product_lot_ids = fields.Many2many('stock.production.lot', 'stock_colis_product_lot_rel', 'lot_id')
    cheque_ids = fields.Many2many('paiement.cheque.client')
    received_cheque_ids = fields.Many2many('paiement.cheque.client', 'colis_received_cheque_rel')
    stock_inventory_source_id = fields.Many2one('stock.inventory', string="Mouvement Source de l'inventaire")
    stock_inventory_dest_id = fields.Many2one('stock.inventory', string="Mouvement Destination de l'inventaire")

    def _compute_is_destinataire(self):
        for rec in self:
            rec.is_destinataire = rec.company_dest_id == self.env.user.company_id

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_company(self.env.company).next_by_code('stock.colis')
        res = super(StockColis, self).create(vals)
        return res

    def action_open(self):
        self.write({
            'state': 'open'
        })

    def action_valid(self):
        self.write({
            'state': 'valid'
        })
        self._process_inventory_lines()
        self._process_cheque_lines()

    def _process_inventory_lines(self):
        source_arr_ids, dest_arr_ids = [], []
        inventory_dest_product_ids, inventory_src_product_ids = [], []
        self = self.sudo()
        for line in self.empreinte_lot_ids + self.product_lot_ids:
            dest_location_stock_id = self.env['stock.location'].sudo().search(
                [('company_id', '=', self.company_dest_id.id), ('usage', '=', 'internal')])
            src_location_stock_id = self.env['stock.location'].sudo().search(
                [('company_id', '=', self.company_id.id), ('usage', '=', 'inventory')], limit=1)

            product_id = self.env['product.template'].search([
                ('name', '=', line.product_id.name)
            ])

            dest_lot = self.env['stock.production.lot'].create({
                'product_id': line.product_id.id,
                'company_id': self.company_dest_id.id,
                'name': line.name
            })

            dest_line_ids = (0, 0, {
                'product_id': product_id.product_variant_id.id,
                'prod_lot_id': dest_lot.id,
                'product_uom_id': product_id.uom_id.id,
                'product_qty': 1,
                'location_id': dest_location_stock_id.id
            })

            dest_arr_ids.append(dest_line_ids)
            inventory_dest_product_ids.append((4, product_id.product_variant_id.id))

            source_line_ids = (0, 0, {
                'product_id': line.product_id.id,
                'prod_lot_id': line.id,
                'product_uom_id': line.product_id.uom_id.id,
                'product_qty': 0,
                'location_id': src_location_stock_id.id
            })

            source_arr_ids.append(source_line_ids)
            inventory_src_product_ids.append((4, line.product_id.id))

        dest_company_mvt = self.sudo().env['stock.inventory'].create({
            'name': self.name + ' DEST',
            'product_ids': inventory_dest_product_ids,
            'company_id': self.company_dest_id.id,
            'colis_id': self.id,
            'line_ids': dest_arr_ids
        })
        self.stock_inventory_dest_id = dest_company_mvt

        dest_company_mvt.action_start()
        dest_company_mvt.action_validate()

        source_company_mvt = self.sudo().env['stock.inventory'].create({
            'name': self.name + ' SRC',
            'product_ids': inventory_src_product_ids,
            'company_id': self.company_id.id,
            'colis_id': self.id,
            'line_ids': source_arr_ids
        })
        self.stock_inventory_source_id = source_company_mvt

        dest_company_mvt.action_start()
        dest_company_mvt.action_validate()

    def _process_cheque_lines(self):
        self = self.sudo()
        cheque_client_obj = self.env['paiement.cheque.client']
        paiement_record_obj = self.env['paiement.record']
        cheques_arr = []
        for record_line in self.cheque_ids:
            journal_id = self.env['account.journal'].search([
                ('name', 'like', record_line.journal_id.name),
                ('company_id', '=', self.company_dest_id.id),
            ])
            vals = {
                'name': record_line.name,
                'amount': record_line.amount,
                'journal_id': journal_id.id,
                'date': record_line.date,
                'client': record_line.client.id,
                'caisse_id': record_line.caisse_id.id,
                'company_id': self.company_dest_id.id,
                'colis_id': self.id,
            }

            if not paiement_record_obj.get_model('cheque', self.company_dest_id.id):
                raise ValidationError(u"Vous devez créer un modèle chèque")
            vals['model_id'] = paiement_record_obj.get_model('cheque', vals['company_id'])
            vals['due_date'] = record_line.due_date
            cheque_id = cheque_client_obj.create(vals)
            cheques_arr.append((4, cheque_id.id))
        self.received_cheque_ids = cheques_arr
        self.cheque_ids.unlink()
