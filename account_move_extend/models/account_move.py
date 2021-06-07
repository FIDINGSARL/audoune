# -*- encoding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from odoo.tools import float_compare


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_payer_frounisseur(self):
        return {
            'name': 'Payer',
            'res_model': 'custom.register.payment',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }