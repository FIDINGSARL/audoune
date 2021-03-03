# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


class PaiementChequeClient(models.Model):
    _inherit = 'paiement.cheque.client'

    colis_request_id = fields.Many2one('stock.colis.request', 'Demande de Colis')


class ColisProduct(models.Model):
    _inherit = 'product.colis'

    colis_request_id = fields.Many2one('stock.colis.request', 'Demande de Colis')


class StockColisRequest(models.Model):
    _name = "stock.colis.request"
    _order = 'create_date desc'
    _description = 'Demande de Colis'
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
    state = fields.Selection([('new', 'Nouveau'), ('open', 'Envoyé'),
                              ('valid', 'Colis en Traitement'),
                              ('done', 'Términé'),
                              ], string=u'État', required=True,
                             copy=False, default='new', track_visibility='onchange',
                             compute="compute_request_done", readonly=False)
    user_id = fields.Many2one('res.users', string='Demandeur', default=lambda self: self.env.user.id)
    user_requested_id = fields.Many2one('res.users', string='Responsable demande')
    request_date = fields.Date('Date demande', default=fields.Date.today())
    is_destinataire = fields.Boolean('Est un destinataire', compute='_compute_is_destinataire')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get(
        'stock.colis.request'), string='Société')
    stock_location_id = fields.Many2one('stock.warehouse', string='Emplacement du responsable')
    stock_location_dest_id = fields.Many2one('stock.warehouse', string='Emplacement du demandeur',
                                             default=_get_user_default_location)
    caisse_id = fields.Many2one('paiement.caisse', string='Caisse du responsable', related='user_requested_id.caisse_id')
    product_line_ids = fields.One2many('product.colis', 'colis_request_id', copy=True)
    cheque_ids = fields.Many2many('paiement.cheque.client', string='Chèques reçus', copy=True)
    stock_colis_id = fields.Many2one('stock.colis', string="Colis", copy=False)
    reliquat_id = fields.Many2one('stock.colis.request', string="Reliquat de")
    is_cheque_only = fields.Boolean(string="Contient juste des chèques", compute='compute_is_cheque_only')
    show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to decide whether the button "Validate" should be displayed.')
    show_send = fields.Boolean(
        compute='_compute_show_send',
        help='Technical field used to decide whether the button "Send" should be displayed.')
    show_draft = fields.Boolean(
        compute='_compute_show_draft',
        help='Technical field used to decide whether the button "Send" should be displayed.')

    @api.onchange('stock_location_id')
    def _compute_user_requested_id(self):
        self = self.sudo()
        res = {}
        res['domain'] = {'user_requested_id': ([('property_warehouse_id', '=', self.stock_location_id.id)])}
        return res

    def _compute_is_destinataire(self):
        for rec in self:
            rec.is_destinataire = rec.stock_location_dest_id == self.env.user.property_warehouse_id

    @api.depends('state')
    def _compute_show_validate(self):
        for rec in self:
            rec.show_validate = False
            if rec.state == 'open' and rec.stock_location_id == self.env.user.property_warehouse_id:
                rec.show_validate = True

    @api.depends('stock_colis_id.stock_picking_id')
    def compute_request_done(self):
        for rec in self:
            if rec.stock_colis_id:
                rec.state = 'valid'
                if not rec.stock_colis_id.is_cheque_only:
                    if rec.stock_colis_id.stock_picking_id.state == 'done':
                        rec.state = 'done'
                else:
                    if rec.stock_colis_id.state == 'valid':
                        rec.state = 'done'
            else:
                rec.state = 'open'

    @api.depends('state')
    def _compute_show_send(self):
        for rec in self:
            rec.show_send = False
            if rec.state == 'new' and rec.stock_location_dest_id in self.env.user.default_location_id:
                rec.show_send = True

    @api.depends('state')
    def _compute_show_draft(self):
        for rec in self:
            rec.show_draft = False
            if rec.state == 'open' and rec.stock_location_dest_id in self.env.user.default_location_id:
                rec.show_draft = True

    @api.depends('product_line_ids')
    def compute_is_cheque_only(self):
        for rec in self:
            rec.is_cheque_only = False
            if not rec.product_line_ids:
                rec.is_cheque_only = True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_company(self.env.company).next_by_code('stock.colis.request')
        res = super(StockColisRequest, self).create(vals)
        return res

    def action_draft(self):
        self.write({
            'state': 'new'
        })

    def action_open(self):
        self.write({
            'state': 'open'
        })

    def action_valid(self):
        self._process_product_lines()
        self.write({
            'state': 'valid'
        })

    def _process_product_lines(self):
        self = self.sudo()
        if self.reliquat_id \
                and not self.reliquat_id.stock_colis_id.is_cheque_only \
                and self.reliquat_id.stock_colis_id.stock_picking_id.state != 'done':
            raise ValidationError('Veuillez tout d\'abord valider le colis de la demande initiale')
        product_line_ids_arr = []
        lot_line_ids_arr = []
        dp_line_ids_arr = []
        cheque_ids_arr = []
        stock_colis_obj = self.env['stock.colis']
        dest_location_stock_id = self.stock_location_dest_id
        src_location_stock_id = self.stock_location_id
        backorder_items_arr = []
        used_serial_numbers = []
        for line in self.product_line_ids:

            if line.product_id.tracking == 'serial':
                """
                    Fetch Stock.quant for any available lot_id in the dest_location_stock_id
                    if found take the first one FIFO
                """
                domain = [
                    ('product_id', '=', line.product_id.id),
                    # ('available_quantity', '>', 0),
                    ('location_id', '=', src_location_stock_id.lot_stock_id.id),
                    ('company_id', '=', self.company_id.id),
                    ('id', 'not in', tuple(used_serial_numbers) if used_serial_numbers else []),
                    ('product_id.is_dp', '=', False)
                ]
                qty_needed = line.product_qty
                if line.product_id.is_dp and line.partner_id:
                    domain = [
                        ('product_id', '=', line.product_id.id),
                        # ('available_quantity', '>', 0),
                        ('location_id', '=', src_location_stock_id.lot_stock_id.id),
                        ('company_id', '=', self.company_id.id),
                        ('id', 'not in', tuple(used_serial_numbers) if used_serial_numbers else []),
                        ('product_id.is_dp', '=', True),
                        ('lot_id.partner_id', '=', line.partner_id.id)
                    ]
                quant_ids = self.env['stock.quant'].search(domain, limit=qty_needed)
                used_serial_numbers.append(quant_ids.mapped('id')[0] if quant_ids.mapped('id') else False)
                if quant_ids:
                    for quant_id in quant_ids:
                        lot_id = quant_id.lot_id
                        if lot_id:
                            if line.partner_id:
                                lot_id.partner_id = line.partner_id
                            if not lot_id.is_dp:
                                lot_line_ids_arr.append((4, lot_id.id))
                            else:
                                dp_line_ids_arr.append((4, lot_id.id))
                qty_to_backorder = line.product_qty - len(quant_ids)

                if qty_to_backorder:
                    backorder_items_arr.append((0, 0, {
                        'product_id': line.product_id.id,
                        'partner_id': line.partner_id.id,
                        'product_qty': qty_to_backorder,
                        'product_uom_id': line.product_uom_id
                    }))

            elif line.product_id.tracking == 'none':
                quant_id = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    # ('available_quantity', '>', line.product_qty),
                    ('location_id', '=', src_location_stock_id.lot_stock_id.id),
                    ('company_id', '=', self.company_id.id),
                ])
                if quant_id:
                    product_line_ids_arr.append((0, 0, {
                        'product_id': quant_id.product_id.id,
                        'product_qty': quant_id.available_quantity if quant_id.available_quantity <= line.product_qty else line.product_qty,
                    }))
                qty_to_backorder = line.product_qty - quant_id.available_quantity if line.product_qty >= quant_id.available_quantity else 0
                if qty_to_backorder:
                    backorder_items_arr.append((0, 0, {
                        'product_id': line.product_id.id,
                        'product_qty': qty_to_backorder,
                        'product_uom_id': line.product_uom_id
                    }))

        for line in self.cheque_ids:
            cheque_ids_arr.append((4, line.id))

        if backorder_items_arr:
            stock_reliquat_id = self.copy()
            stock_reliquat_id.product_line_ids.unlink()
            stock_reliquat_id.cheque_ids.unlink()
            stock_reliquat_id.state = 'open'
            stock_reliquat_id.name = 'REL/' + self.name
            stock_reliquat_id.product_line_ids = backorder_items_arr
            stock_reliquat_id.reliquat_id = self.id

        stock_colis_dict = {
            'name': self.name,
            'stock_location_id': src_location_stock_id.id,
            'stock_location_dest_id': dest_location_stock_id.id,
            'company_id': self.env.company.id,
            'is_cheque_only': self.is_cheque_only,
            'user_requesting_id': self.user_id.id
        }
        if lot_line_ids_arr or product_line_ids_arr or dp_line_ids_arr:
            stock_colis_dict.update({
                'product_lot_ids': lot_line_ids_arr,
                'product_line_ids': product_line_ids_arr,
                'dossier_physique': dp_line_ids_arr,
            })
        else:
            if not self.is_cheque_only:
                raise ValidationError('Aucune quantité disponible')
            else:

                stock_colis_dict.update({
                    'cheque_ids': cheque_ids_arr
                })

        stock_colis_id = stock_colis_obj.create(stock_colis_dict)
        self.stock_colis_id = stock_colis_id
