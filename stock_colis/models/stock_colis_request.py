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
                              ('valid', 'Validé par le centre')], string=u'État', required=True,
                             copy=False, default='new', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Demandeur', default=lambda self: self.env.user.id)
    user_requested_id = fields.Many2one('res.users', string='Responsable demande')
    request_date = fields.Date('Date demande', default=fields.Date.today())
    is_destinataire = fields.Boolean('Est un destinataire', compute='_compute_is_destinataire')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('stock.colis.request'), string='Société')
    stock_location_id = fields.Many2one('stock.warehouse', string='Emplacement')
    stock_location_dest_id = fields.Many2one('stock.warehouse', string='Emplacement de destination', default=_get_user_default_location)
    product_line_ids = fields.One2many('product.colis', 'colis_request_id')
    cheque_ids = fields.Many2many('paiement.cheque.client', string='Chèques reçus')
    stock_colis_id = fields.Many2one('stock.colis', string="Colis")
    reliquat_id = fields.Many2one('stock.colis.request', string="Reliquat de")
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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_company(self.env.company).next_by_code('stock.colis')
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
        self.write({
            'state': 'valid'
        })
        self._process_product_lines()

    def _process_product_lines(self):
        if self.reliquat_id and self.reliquat_id.stock_colis_id.tock_picking_id.state != 'done':
            raise ValidationError('Veuillez tout d\'abord valider le colis de la demande initiale')

        product_line_ids_arr = []
        lot_line_ids_arr = []
        dp_line_ids_arr = []
        cheque_ids_arr = []
        self = self.sudo()
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
                qty_needed = line.product_qty
                quant_ids = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    # ('available_quantity', '>', 0),
                    ('location_id', '=', src_location_stock_id.lot_stock_id.id),
                    ('company_id', '=', self.company_id.id),
                    ('id', 'not in', tuple(used_serial_numbers) if used_serial_numbers else []),
                ], limit=qty_needed)
                print('product_id', line.product_id.name)
                print('quant_ids', quant_ids)
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
            stock_reliquat_id.state = 'open'
            stock_reliquat_id.name = 'REL/' + self.name
            stock_reliquat_id.product_line_ids = backorder_items_arr
            stock_reliquat_id.reliquat_id = self.id

        stock_colis_id = stock_colis_obj.create({
            'name': self.name,
            'stock_location_id': src_location_stock_id.id,
            'stock_location_dest_id': dest_location_stock_id.id,
            'product_lot_ids': lot_line_ids_arr,
            'product_line_ids': product_line_ids_arr,
            'dossier_physique': dp_line_ids_arr,
            'cheque_ids': cheque_ids_arr,
            'company_id': self.env.company.id
        })
        self.stock_colis_id = stock_colis_id