# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


class DossierRembourssement(models.Model):
    _name = "dossier.rembourssement"

    name = fields.Char('Référence', readonly=1)
    description = fields.Char('Description')
    partner_id = fields.Many2one('res.partner', string='Client')
    amount = fields.Float('Montant')
    assurance_id = fields.Many2one('pec.assurance', string="Assurance")
    date = fields.Date('Date')
    task_id = fields.Many2one('project.task', string="État du Dossier")

    @api.model
    def create(self, vals):
        vals['name'] = self.env.ref('dossier_rembourssement.seq_dr').next_by_code('dossier.rembourssement') or ''
        assurance_id = self.env['pec.assurance'].browse(vals['assurance_id'])
        partner_id = self.env['res.partner'].browse(self._context.get('default_partner_id')) or self.env['res.partner'].browse(vals['partner_id'])
        if assurance_id:
            project_id = self.env.ref(
                'project_extend.project_non_soumise') if assurance_id.type == 'non_soumise' else self.env.ref(
                'project_extend.project_soumise')
            stage_id = self.env.ref(
                'project_extend.ns_stage_1') if assurance_id.type == 'non_soumise' else self.env.ref(
                'project_extend.s_stage_1')
        else:
            project_id = self.env.ref('project_extend.project_partie_client')
            stage_id = self.env.ref('project_extend.pc_stage_1')

        task_id = self.env['project.task'].create({
            'project_id': project_id.id,
            'name': partner_id.name + ' ' + assurance_id.name if assurance_id else partner_id.name + ' partie client',
            'partner_id': partner_id.id,
            'stage_id': stage_id.id,
            # 'pec_id': vals['id']
        })
        vals['task_id'] = task_id.id
        res = super(DossierRembourssement, self).create(vals)
        task_id.write({
            'dr_id': res.id
        })
        task_id.activity_schedule(
                 activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                 summary=stage_id.name + ' ' + partner_id.name,
                 user_id=task_id.user_id.id)
        return res

    @api.onchange('partner_id')
    def _compute_parent_assurances(self):
        self.assurance_id = False
        res = {'domain': {}}
        res['domain'] = {'assurance_id': [('id', 'in', self.partner_id.assurance_ids.mapped('assurance_id').ids)]}
        return res
