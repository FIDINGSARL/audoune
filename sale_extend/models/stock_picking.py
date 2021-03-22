# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        if self.sale_id:
            for line in self.sudo().move_line_ids:
                if line.lot_id:
                    lot_id = line.lot_id
                    if not lot_id.partner_id:
                        raise ValidationError('Veuillez contactez votre administrateur '
                                              'pour attribuer un client à ce numéro de série')
                    else:
                        if lot_id.partner_id != self.partner_id:
                            raise ValidationError("Le numéro de lot %s de l'article %s ne correspond pas au client %s"
                                                  % (lot_id.name, lot_id.product_id.name, self.partner_id.name))
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    partner_id = fields.Many2one('res.partner', related='picking_id.partner_id', string='Client')

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('move_id'):
    #             vals['company_id'] = self.env['stock.move'].browse(vals['move_id']).company_id.id
    #         elif vals.get('picking_id'):
    #             vals['company_id'] = self.env['stock.picking'].browse(vals['picking_id']).company_id.id
    #
    #         if vals.get('lot_id', False) and vals.get('picking_id', False):
    #             lot_id = self.env['stock.production.lot'].browse(vals['lot_id'])
    #             picking_id = self.env['stock.picking'].browse(vals['picking_id'])
    #             if lot_id and picking_id:
    #                 quantity_available = sum(lot_id.quant_ids.mapped('available_quantity'))
    #                 if lot_id.partner_id == picking_id.partner_id:
    #                     print('lot ids look alike')
    #                 else:
    #                     vals['lot_id'] = False
    #     mls = super().create(vals_list)
    #
    #     def create_move(move_line):
    #         new_move = self.env['stock.move'].create({
    #             'name': _('New Move:') + move_line.product_id.display_name,
    #             'product_id': move_line.product_id.id,
    #             'product_uom_qty': 0 if move_line.picking_id and move_line.picking_id.state != 'done' else move_line.qty_done,
    #             'product_uom': move_line.product_uom_id.id,
    #             'description_picking': move_line.description_picking,
    #             'location_id': move_line.picking_id.location_id.id,
    #             'location_dest_id': move_line.picking_id.location_dest_id.id,
    #             'picking_id': move_line.picking_id.id,
    #             'state': move_line.picking_id.state,
    #             'picking_type_id': move_line.picking_id.picking_type_id.id,
    #             'restrict_partner_id': move_line.picking_id.owner_id.id,
    #             'company_id': move_line.picking_id.company_id.id,
    #         })
    #         move_line.move_id = new_move.id
    #
    #     # If the move line is directly create on the picking view.
    #     # If this picking is already done we should generate an
    #     # associated done move.
    #     for move_line in mls:
    #         if move_line.move_id or not move_line.picking_id:
    #             continue
    #         if move_line.picking_id.state != 'done':
    #             moves = move_line.picking_id.move_lines.filtered(lambda x: x.product_id == move_line.product_id)
    #             moves = sorted(moves, key=lambda m: m.quantity_done < m.product_qty, reverse=True)
    #             if moves:
    #                 move_line.move_id = moves[0].id
    #             else:
    #                 create_move(move_line)
    #         else:
    #             create_move(move_line)
    #
    #     for ml, vals in zip(mls, vals_list):
    #         if ml.move_id and \
    #                 ml.move_id.picking_id and \
    #                 ml.move_id.picking_id.immediate_transfer and \
    #                 ml.move_id.state != 'done' and \
    #                 'qty_done' in vals:
    #             ml.move_id.product_uom_qty = ml.move_id.quantity_done
    #         if ml.state == 'done':
    #             if 'qty_done' in vals:
    #                 ml.move_id.product_uom_qty = ml.move_id.quantity_done
    #             if ml.product_id.type == 'product':
    #                 Quant = self.env['stock.quant']
    #                 quantity = ml.product_uom_id._compute_quantity(ml.qty_done, ml.move_id.product_id.uom_id,rounding_method='HALF-UP')
    #                 in_date = None
    #                 available_qty, in_date = Quant._update_available_quantity(ml.product_id, ml.location_id, -quantity, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #                 if available_qty < 0 and ml.lot_id:
    #                     # see if we can compensate the negative quants with some untracked quants
    #                     untracked_qty = Quant._get_available_quantity(ml.product_id, ml.location_id, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id, strict=True)
    #                     if untracked_qty:
    #                         taken_from_untracked_qty = min(untracked_qty, abs(quantity))
    #                         Quant._update_available_quantity(ml.product_id, ml.location_id, -taken_from_untracked_qty, lot_id=False, package_id=ml.package_id, owner_id=ml.owner_id)
    #                         Quant._update_available_quantity(ml.product_id, ml.location_id, taken_from_untracked_qty, lot_id=ml.lot_id, package_id=ml.package_id, owner_id=ml.owner_id)
    #                 Quant._update_available_quantity(ml.product_id, ml.location_dest_id, quantity, lot_id=ml.lot_id, package_id=ml.result_package_id, owner_id=ml.owner_id, in_date=in_date)
    #             next_moves = ml.move_id.move_dest_ids.filtered(lambda move: move.state not in ('done', 'cancel'))
    #             next_moves._do_unreserve()
    #             next_moves._action_assign()
    #     return mls
    #




