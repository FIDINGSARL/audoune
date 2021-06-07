# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    responsable_centre_id = fields.Many2one('res.users', 'Responsable de centre')

    @api.model
    def create(self, vals):
        vals['user_id'] = False
        return super(CrmLead, self).create(vals)

    def write(self, vals):
        resp_id = self.env['res.users'].browse(vals.get('responsable_centre_id')) \
            if vals.get('responsable_centre_id', False) else self.responsable_centre_id
        if resp_id and self.partner_id:
            self.partner_id.write({
                'user_id': resp_id.id
            })
        if vals.get('stage_id'):
            stage_id = self.env['crm.stage'].browse(vals['stage_id'])
            centre_stage_id = self.env.ref('crm_extend.lead_stage_centre')
            quali_stage_id = self.env.ref('crm_extend.lead_stage_qualification')
            relance_stage_id = self.env.ref('crm_extend.lead_stage_relance')
            if stage_id == centre_stage_id:
                if not resp_id:
                    raise ValidationError('Veuillez remplir le champs Résponsable du centre')
                partner_id = self.env['res.partner'].create({
                    'name': self.name,
                    'user_id': resp_id.id,
                    'phone': self.phone,
                    'email': self.email_from,
                    'see_all': True,
                    'type': 'contact'
                })
                self.activity_schedule(
                    activity_type_id=self.env.ref('mail.mail_activity_data_meeting').id,
                    summary=('RDV avec le client %s' % self.name),
                    user_id=resp_id.id)
                self.partner_id = partner_id
            if stage_id == quali_stage_id:
                self.user_id = self.env.user.id
            if stage_id == relance_stage_id:
                self.activity_schedule(
                    activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                    summary=('Relance du client %s' % self.name),
                    user_id=resp_id.id)
        return super(CrmLead, self).write(vals)
