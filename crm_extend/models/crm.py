# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    responsable_centre_id = fields.Many2one('res.users', 'Responsable de centre')

    @api.depends('user_id', 'type')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for lead in self:
            # setting user as void should not trigger a new team computation
            # if not lead.user_id:
            #     continue
            # user = lead.user_id
            # if lead.team_id and user in lead.team_id.member_ids | lead.team_id.user_id:
            #     continue
            # team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            # team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=team_domain)
            lead.team_id = self.env.ref('crm_extend.team_centre_appel').id

    @api.depends('team_id', 'type')
    def _compute_stage_id(self):
        for lead in self:
            if not lead.stage_id:
                lead.stage_id = self.env.ref('crm_extend.lead_stage_nouveau').id

    @api.model
    def create(self, vals):
        vals['user_id'] = False
        vals['team_id'] = self.env.ref('crm_extend.team_centre_appel').id
        vals['stage_id'] = self.env.ref('crm_extend.lead_stage_nouveau').id
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
                    summary=('%s RDV' % self.name),
                    user_id=resp_id.id)
                self.partner_id = partner_id
                self.team_id = self.env.ref('crm_extend.team_centre').id
            if stage_id == quali_stage_id:
                self.user_id = self.env.user.id
            # if stage_id == relance_stage_id:
            #     self.activity_schedule(
            #         activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
            #         summary=('Relance du client %s' % self.name),
            #         user_id=resp_id.id)
        return super(CrmLead, self).write(vals)

    def create_auto_crm_activity(self):
        lead_relance_ids = self.env['crm.lead'].search(
            [('stage_id', '=', self.env.ref('crm_extend.lead_stage_relance').id)])
        lead_nrp_ids = self.env['crm.lead'].search([('stage_id', '=', self.env.ref('crm_extend.lead_stage_nrp').id)])
        for rec in lead_relance_ids:
            activity_relance_ids = rec.activity_ids.filtered(
                lambda activity: activity.activity_type_id == self.env.ref('crm_extend.mail_activity_type_relance'))
            if len(activity_relance_ids):
                if len(activity_relance_ids) >= 5:
                    rec.write({
                        'stage_id': self.env.ref('crm_extend.lead_stage_quarantine').id
                    })
                elif len(activity_relance_ids) < 5:
                    recent_date = max(activity_relance_ids.mapped('date_deadline'))
                    print('recent_date', recent_date)
                    if recent_date and (fields.date.today() - recent_date).days > 7:
                        rec.activity_schedule(
                            activity_type_id=self.env.ref('crm_extend.mail_activity_type_relance').id,
                            summary='Relance du client %s' % (rec.partner_id.name if rec.partner_id else rec.name),
                            user_id=rec.responsable_centre_id.id if rec.responsable_centre_id else rec.user_id.id,
                            date_deadline=recent_date + datetime.timedelta(weeks=1)
                        )

        for rec in lead_nrp_ids:
            activity_nrp_ids = rec.activity_ids.filtered(
                lambda activity: activity.activity_type_id == self.env.ref('crm_extend.mail_activity_type_nrp'))

            if len(activity_nrp_ids):
                if len(activity_nrp_ids) >= 5:
                    rec.write({
                        'stage_id': self.env.ref('crm_extend.lead_stage_quarantine').id
                    })
                elif len(activity_nrp_ids) < 5:
                    recent_date = max(activity_nrp_ids.mapped('date_deadline'))
                    if recent_date and (fields.date.today() - recent_date).days >= 1:
                        rec.activity_schedule(
                            activity_type_id=self.env.ref('crm_extend.mail_activity_type_nrp').id,
                            summary='NRP du client %s' % (rec.partner_id.name if rec.partner_id else rec.name),
                            user_id=rec.responsable_centre_id.id if rec.responsable_centre_id else rec.user_id.id,
                            date_deadline=recent_date + datetime.timedelta(days=1)
                        )
            else:
                rec.activity_schedule(
                    activity_type_id=self.env.ref('crm_extend.mail_activity_type_nrp').id,
                    summary='NRP du client %s' % (rec.partner_id.name if rec.partner_id else rec.name),
                    user_id=rec.responsable_centre_id.id if rec.responsable_centre_id else rec.user_id.id,
                    date_deadline=fields.date.today() + datetime.timedelta(days=1)
                )
