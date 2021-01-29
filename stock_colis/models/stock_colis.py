# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    default_location_id = fields.Many2one('stock.location', string='Emplacement de l\'utilisateur')


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
    is_destinataire = fields.Boolean('Est un destinataire', compute='_compute_is_destinataire')
    stock_location_id = fields.Many2one('stock.location', string='Société', default=lambda self: self.env.user.default_location_id.id)
    stock_location_dest_id = fields.Many2one('stock.location', string='Société de destination')
    dossier_physique = fields.One2many('dossier.physique', 'colis_id')
    empreinte_lot_ids = fields.Many2many('stock.production.lot', 'stock_colis_empreinte_lot_rel', 'lot_id')
    product_lot_ids = fields.Many2many('stock.production.lot', 'stock_colis_product_lot_rel', 'lot_id')
    cheque_ids = fields.Many2many('paiement.cheque.client', string='Chèques reçus')
    received_cheque_ids = fields.Many2many('paiement.cheque.client', 'colis_received_cheque_rel', string="Chèques reçus")
    stock_picking_id = fields.Many2one('stock.picking', string="Mouvement Source de l'inventaire")
    show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to decide whether the button "Validate" should be displayed.')
    show_send = fields.Boolean(
        compute='_compute_show_send',
        help='Technical field used to decide whether the button "Send" should be displayed.')

    def _compute_is_destinataire(self):
        for rec in self:
            rec.is_destinataire = rec.stock_location_dest_id == self.env.user.default_location_id

    @api.depends('state')
    def _compute_show_validate(self):
        for rec in self:
            rec.show_validate = False
            if rec.state == 'open' and rec.stock_location_dest_id == self.env.user.default_location_id:
                rec.show_validate = True

    @api.depends('state')
    def _compute_show_send(self):
        for rec in self:
            rec.show_send = False
            if rec.state == 'new' and rec.stock_location_id == self.env.user.default_location_id:
                rec.show_send = True

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
        line_ids_arr = []
        move_ids_arr = []
        self = self.sudo()
        picking_obj = self.env['stock.picking']
        dest_location_stock_id = self.stock_location_dest_id.id
        src_location_stock_id = self.stock_location_id.id
        picking_type = self.env.ref('stock.picking_type_internal').id
        for line in self.empreinte_lot_ids + self.product_lot_ids:

            move_line_ids_without_package = (0, 0, {
                # 'name': 'Réassort ' + line.name,
                'product_id': line.product_id.id,
                'lot_id': line.id,
                'product_uom_qty': 0,
                'product_uom_id': line.product_id.uom_id.id,
                'location_dest_id': dest_location_stock_id,
                'location_id': src_location_stock_id
            })

            move_ids_without_package = (0, 0, {
                'name': 'Réassort',
                'product_id': line.product_id.id,
                'product_uom_qty': 1,
                'product_uom': line.product_id.uom_id.id,
                'location_dest_id': dest_location_stock_id,
                'location_id': src_location_stock_id
            })

            line_ids_arr.append(move_line_ids_without_package)
            move_ids_arr.append(move_ids_without_package)

        picking_id = picking_obj.create({
            'location_id': src_location_stock_id,
            'location_dest_id': dest_location_stock_id,
            'picking_type_id': picking_type,
            'move_line_ids_without_package': line_ids_arr,
            'move_ids_without_package': move_ids_arr
        })

        picking_id.action_confirm()
        picking_id.action_assign()
        # picking_id.button_validate()
        self.stock_picking_id = picking_id

    def _process_cheque_lines(self):
        self = self.sudo()
        cheque_client_obj = self.env['paiement.cheque.client']
        paiement_record_obj = self.env['paiement.record']
        cheques_arr = []
        for record_line in self.cheque_ids:
            journal_id = self.env['account.journal'].search([
                ('name', 'like', record_line.journal_id.name),
                ('company_id', '=', self.env.user.company_id.id),
            ])
            vals = {
                'name': record_line.name,
                'amount': record_line.amount,
                'journal_id': journal_id.id,
                'date': record_line.date,
                'client': record_line.client.id,
                'caisse_id': record_line.caisse_id.id,
                'company_id': self.env.user.company_id.id,
                'colis_id': self.id,
            }

            if not paiement_record_obj.get_model('cheque', self.env.user.company_id.id):
                raise ValidationError(u"Vous devez créer un modèle chèque")
            vals['model_id'] = paiement_record_obj.get_model('cheque', vals['company_id'])
            vals['due_date'] = record_line.due_date
            cheque_id = cheque_client_obj.create(vals)
            cheques_arr.append((4, cheque_id.id))
        self.received_cheque_ids = cheques_arr
        self.cheque_ids.unlink()


class DossierPhysique(models.Model):
    _name = 'dossier.physique'

    name = fields.Char('Description')
    partner_id = fields.Many2one('res.partner', 'Patient')
    colis_id = fields.Many2one('stock.colis', 'Colis')
