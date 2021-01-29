# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
