# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

from odoo.odoo import tools


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    can_write = fields.Boolean(compute='_compute_can_write', help='Technical field to hide buttons if the current user has no access.')
    is_my_activity = fields.Boolean('Mon activité', compute='compute_is_my_activity')

    def compute_is_my_activity(self):
        for rec in self:
            rec.is_my_activity = self.create_uid == self.env.user

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

    @api.onchange('activity_type_id')
    def _onchange_activity_type_id(self):
        if self.activity_type_id:
            if self.activity_type_id.summary:
                self.summary = self.activity_type_id.summary
            self.date_deadline = self._calculate_date_deadline(self.activity_type_id)
            moderer_type_id = self.env.ref('crm_extend.mail_activity_type_moderer')
            if self.res_model == 'res.partner' and self.res_id and self.activity_type_id != moderer_type_id:
                partner_id = self.env['res.partner'].browse(self.res_id)
                if partner_id.user_id:
                    self.user_id = partner_id.user_id
            else:
                self.user_id = self.activity_type_id.default_user_id or self.env.user
            if self.activity_type_id.default_description:
                self.note = self.activity_type_id.default_description

    def action_create_calendar_event(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("calendar.action_calendar_event")
        crm_id = self.env[self.env.context.get('default_res_model')].browse(self.env.context.get('default_res_id'))
        action['context'] = {
            'default_activity_type_id': self.activity_type_id.id,
            'default_res_id': self.env.context.get('default_res_id'),
            'default_res_model': self.env.context.get('default_res_model'),
            'default_name': self.summary or self.res_name,
            'default_description': self.note and tools.html2plaintext(self.note).strip() or '',
            'default_activity_ids': [(6, 0, self.ids)],
        }
        if crm_id:
            action['context']['default_partner_ids'] = [(6, 0, [crm_id.responsable_centre_id.partner_id.id])]
            action['context']['default_user_id'] = crm_id.responsable_centre_id.id
        print('action', action['context'])
        return action
