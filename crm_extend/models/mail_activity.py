# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    can_write = fields.Boolean(compute='_compute_can_write', help='Technical field to hide buttons if the current user has no access.')

    @api.depends('res_model', 'res_id', 'user_id')
    def _compute_can_write(self):
        valid_records = self._filter_access_rules('write')
        for record in self:
            moderate_activity_type = self.env.ref('crm_extend.mail_activity_type_moderer')
            if moderate_activity_type == record.activity_type_id:
                can_moderate = self.env.user.has_group('crm_extend.group_activity_moderate')
                record.can_write = can_moderate
            else:
                record.can_write = record in valid_records