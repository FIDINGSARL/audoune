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
        if vals.get('stage_id'):
            stage_id = self.env['crm.stage'].browse(vals['stage_id'])
            centre_stage_id = self.env.ref('crm_extend.lead_stage_centre')
            quali_stage_id = self.env.ref('crm_extend.lead_stage_qualification')
            if stage_id == centre_stage_id:
                partner_id = self.env['res.partner'].create({
                    'name': self.name,
                    'user_id': self.responsable_centre_id.id,
                    'phone': self.phone,
                    'email': self.email_from,
                    'see_all': True,
                    'type': 'contact'
                })
                self.partner_id = partner_id
            if stage_id == quali_stage_id:
                self.user_id = self.env.user.id
        return super(CrmLead, self).write(vals)



