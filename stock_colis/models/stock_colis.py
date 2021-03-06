# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    default_location_id = fields.Many2many('stock.warehouse', 'res_user_stock_warehouse_rel',
                                           string='Emplacements de l\'utilisateur')


class PaiementChequeClient(models.Model):
    _inherit = 'paiement.cheque.client'

    colis_id = fields.Many2one('stock.colis', 'Colis d\'origine')


class StockColis(models.Model):
    _name = "stock.colis"
    _order = 'create_date desc'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_user_default_location(self):
        user_id = self.env.user
        company_id = self.env.company
        user_warehouse_id = False
        if user_id.default_location_id:
            user_warehouse_id = user_id.default_location_id.filtered(
                lambda warehouse: company_id == warehouse.company_id)
        if user_warehouse_id:
            return user_warehouse_id.id
        else:
            return False

    name = fields.Char('Référence', readonly=1)
    state = fields.Selection([('new', 'Nouveau'), ('open', 'Envoyé au Demandeur'),
                              ('valid', 'Validé par le Demandeur')], string=u'État', required=True,
                             copy=False, default='new', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Emetteur', default=lambda self: self.env.user.id)
    user_requesting_id = fields.Many2one('res.users', string='Destinataire')
    is_destinataire = fields.Boolean('Est un destinataire', compute='_compute_is_destinataire')
    # company_id = fields.Many2one('res.company', default=lambda self: self.env.company, string='Société')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('stock.colis'), string='Société')
    stock_location_id = fields.Many2one('stock.warehouse', string='Emplacement', default=_get_user_default_location)
    stock_location_dest_id = fields.Many2one('stock.warehouse', string='Emplacement de destination')
    dossier_physique = fields.One2many('stock.colis.line', 'dp_colis_id', string='Dossiers physiques')
    product_lot_ids = fields.One2many('stock.colis.line', 'lot_colis_id', string='Numéros de série')
    product_line_ids = fields.One2many('product.colis', 'colis_id')
    cheque_ids = fields.Many2many('paiement.cheque.client', string='Chèques reçus')
    received_cheque_ids = fields.Many2many('paiement.cheque.client', 'colis_received_cheque_rel',
                                           string="Chèques reçus")
    stock_picking_id = fields.Many2one('stock.picking', string="Mouvement Source de l'inventaire")
    is_cheque_only = fields.Boolean(string="Contient juste des chèques", compute='compute_is_cheque_only')
    show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to decide whether the button "Validate" should be displayed.')
    show_send = fields.Boolean(
        compute='_compute_show_send',
        help='Technical field used to decide whether the button "Send" should be displayed.')

    def _compute_is_destinataire(self):
        for rec in self:
            rec.is_destinataire = rec.stock_location_dest_id == self.env.user.property_warehouse_id

    @api.onchange('stock_location_dest_id')
    def _compute_user_requested_id(self):
        self = self.sudo()
        res = {}
        res['domain'] = {'user_requesting_id': ([('property_warehouse_id', '=', self.stock_location_dest_id.id)])}
        return res

    @api.depends('state')
    def _compute_show_validate(self):
        for rec in self:
            rec.show_validate = False
            if rec.state == 'open' and rec.stock_location_dest_id == self.env.user.property_warehouse_id:
                rec.show_validate = True

    @api.depends('state')
    def _compute_show_send(self):
        for rec in self:
            rec.show_send = False
            if rec.state == 'new' and rec.stock_location_id in self.env.user.default_location_id:
                rec.show_send = True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_company(self.env.company).next_by_code('stock.colis')
        res = super(StockColis, self).create(vals)
        return res

    @api.depends('product_lot_ids', 'dossier_physique', 'product_line_ids')
    def compute_is_cheque_only(self):
        for rec in self:
            rec.is_cheque_only = False
            if not rec.product_lot_ids and not rec.dossier_physique and not rec.product_line_ids:
                rec.is_cheque_only = True

    def action_open(self):
        lot_partner_missing = self.product_lot_ids.filtered(lambda line: not line.partner_id)
        dp_partner_missing = self.dossier_physique.filtered(lambda line: not line.partner_id)
        if lot_partner_missing or dp_partner_missing:
            raise ValidationError('Veuillez remplir le champs client dans les lignes des prothèses ou dossiers physiques')
        self.write({
            'state': 'open'
        })

    def action_valid(self):
        self.write({
            'state': 'valid'
        })
        self._process_cheque_lines()
        if not self.is_cheque_only:
            self._process_lot_lines()

    def _process_lot_lines(self):
        line_ids_arr = []
        move_ids_arr = []
        self = self.sudo()
        picking_obj = self.env['stock.picking']
        dest_location_stock_id = self.env['stock.warehouse'].browse(self.stock_location_dest_id.id)
        src_location_stock_id = self.env['stock.warehouse'].browse(self.stock_location_id.id)
        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal'),
                                                              ('company_id', '=', self.env.company.id),
                                                              ('warehouse_id', '=', self.stock_location_id.id),
                                                              ])
        for line in self.product_lot_ids + self.dossier_physique:

            line.lot_id.partner_id = line.partner_id

            move_line_ids_without_package = (0, 0, {
                'product_id': line.product_id.id,
                'lot_id': line.lot_id.id,
                'product_uom_qty': 0,
                'product_uom_id': line.product_id.uom_id.id,
                'location_dest_id': dest_location_stock_id.lot_stock_id.id,
                'location_id': src_location_stock_id.lot_stock_id.id
            })

            move_ids_without_package = (0, 0, {
                'name': 'Réassort',
                'product_id': line.product_id.id,
                'product_uom_qty': 1,
                'product_uom': line.product_id.uom_id.id,
                'location_dest_id': dest_location_stock_id.lot_stock_id.id,
                'location_id': src_location_stock_id.lot_stock_id.id
            })

            line_ids_arr.append(move_line_ids_without_package)
            move_ids_arr.append(move_ids_without_package)

        for line in self.product_line_ids:
            product_move_ids_without_package = (0, 0, {
                'name': 'Réassort Articles',
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_qty,
                'product_uom': line.product_id.uom_id.id,
                'location_dest_id': dest_location_stock_id.lot_stock_id.id,
                'location_id': src_location_stock_id.lot_stock_id.id
            })

            move_ids_arr.append(product_move_ids_without_package)

        picking_id = picking_obj.create({
            'location_id': src_location_stock_id.lot_stock_id.id,
            'location_dest_id': dest_location_stock_id.lot_stock_id.id,
            'picking_type_id': picking_type.id,
            'move_line_ids_without_package': line_ids_arr,
            'move_ids_without_package': move_ids_arr,
            'colis_id': self.id
        })
        picking_id.with_context(default_picking_type_id=picking_type).write({
            'company_id': self.env.company.id
        })
        picking_id.action_confirm()
        picking_id.action_assign()
        picking_id.button_validate()
        self.stock_picking_id = picking_id

    def _process_cheque_lines(self):
        self = self.sudo()
        for cheque in self.cheque_ids:
            cheque.write({
                'caisse_id': self.user_requesting_id.caisse_id.id
            })


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    colis_id = fields.Many2one('stock.colis', 'Colis')


class StockProductionLot(models.Model):
    _name = 'stock.colis.line'

    lot_colis_id = fields.Many2one('stock.colis', 'Colis lot')
    dp_colis_id = fields.Many2one('stock.colis', 'Colis dp')
    product_id = fields.Many2one('product.product', 'Article')
    lot_id = fields.Many2one('stock.production.lot', 'Numéro de série')
    partner_id = fields.Many2one('res.partner', 'Patient', related='lot_id.partner_id', readonly=False)
    available_qty = fields.Float(related='lot_id.available_qty', string='Quantité disponible')


class ColisProduct(models.Model):
    _name = 'product.colis'

    colis_id = fields.Many2one('stock.colis', 'Colis')
    product_id = fields.Many2one('product.product', 'Article')
    tracking = fields.Selection(string='Product Tracking', readonly=True, related="product_id.tracking")
    product_uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', stirng='Unité de mesure')
    product_qty = fields.Float('Quantité', default=1.0)
    partner_id = fields.Many2one('res.partner', string="Patient")
