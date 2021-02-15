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
    user_requested_id = fields.Many2one('res.users', string='Responsable demande', compute='_compute_user_requested_id')
    request_date = fields.Date('Date demande', default=fields.Date.today())
    is_destinataire = fields.Boolean('Est un destinataire', compute='_compute_is_destinataire')
    company_id = fields.Many2one('res.company', default=lambda self: self.env['res.company']._company_default_get('stock.colis.request'), string='Société')
    stock_location_id = fields.Many2one('stock.warehouse', string='Emplacement')
    stock_location_dest_id = fields.Many2one('stock.warehouse', string='Emplacement de destination', default=_get_user_default_location)
    product_line_ids = fields.One2many('product.colis', 'colis_request_id')
    cheque_ids = fields.Many2many('paiement.cheque.client', string='Chèques reçus')
    stock_colis_id = fields.Many2one('stock.colis', string="Colis")
    show_validate = fields.Boolean(
        compute='_compute_show_validate',
        help='Technical field used to decide whether the button "Validate" should be displayed.')
    show_send = fields.Boolean(
        compute='_compute_show_send',
        help='Technical field used to decide whether the button "Send" should be displayed.')

    @api.depends('stock_location_id')
    def _compute_user_requested_id(self):
        self = self.sudo()
        for rec in self:
            rec.user_requested_id = self.env['res.users'].search([('property_warehouse_id', '=', self.stock_location_id.id)],
                                                      limit=1)

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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_company(self.env.company).next_by_code('stock.colis')
        res = super(StockColisRequest, self).create(vals)
        return res

    def action_open(self):
        for line in self.product_line_ids:
            self.activity_schedule(
                'stock_colis.mail_activity_colis',
                summary="%d de %s : %s" % (line.product_qty, line.product_id.name, self.name),
                note="Vous avez été assigné à la préparation de l'article %s du colis numéro %s" % (line.product_id.name, self.name),
                date_deadline=self.request_date,
                user_id=self.user_requested_id.id,
            )
        self.write({
            'state': 'open'
        })

    def action_valid(self):
        self.write({
            'state': 'valid'
        })
        self._process_product_lines()

    def _process_product_lines(self):
        product_line_ids_arr = []
        lot_line_ids_arr = []
        dp_line_ids_arr = []
        cheque_ids_arr = []
        self = self.sudo()
        stock_colis_obj = self.env['stock.colis']
        dest_location_stock_id = self.stock_location_dest_id
        src_location_stock_id = self.stock_location_id
        for line in self.product_line_ids:
            if line.product_id.tracking == 'serial':
                """
                    Fetch Stock.quant for any available lot_id in the dest_location_stock_id
                    if found take the first one FIFO
                """
                quant_id = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('available_quantity', '>', 0),
                    ('location_id', '=', src_location_stock_id.lot_stock_id.id),
                    ('company_id', '=', self.company_id.id),
                ], limit=1)
                if quant_id:
                    lot_id = quant_id.lot_id
                    if lot_id:
                        if not lot_id.is_dp:
                            lot_line_ids_arr.append((4, lot_id.id))
                        else:
                            dp_line_ids_arr.append((4, lot_id.id))
                else:
                    raise ValidationError('Vous n\'avez pas sufisement de quantité de l\'article %s dans votre stock' % line.product_id.name)
            elif line.product_id.tracking == 'none':
                quant_id = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('available_quantity', '>', line.product_qty),
                    ('location_id', '=', src_location_stock_id.lot_stock_id.id),
                    ('company_id', '=', self.company_id.id),
                ])
                if quant_id:
                    product_line_ids_arr.append((0, 0, {
                        'product_id': quant_id.product_id.id,
                        'product_qty': line.product_qty,
                    }))
                else:
                    raise ValidationError('Vous n\'avez pas sufisement de quantité de l\'article %s dans votre stock' % line.product_id.name)

        for line in self.cheque_ids:
            cheque_ids_arr.append((4, line.id))

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