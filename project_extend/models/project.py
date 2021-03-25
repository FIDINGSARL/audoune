# -*- encoding: utf-8 -*-

from odoo import models,fields, api
from datetime import datetime


class ProjectTask(models.Model):
    _inherit = 'project.task'

    dr_id = fields.Many2one('dossier.rembourssement', string="Dossier de Rembourssement")
    assurance_id = fields.Many2one('pec.assurance', related='dr_id.assurance_id', string="Assurance")
    accorde_task_id = fields.Many2one('project.task', 'Provenant de l\'accord')

    @api.model
    def _attente_remboursement_cron(self):
        tasks = self.env['project.task'].search([])
        for task in tasks:
            current_stage_id = self.env.ref('project_extend.ns_stage_3') if task.assurance_id.type == 'non_soumise' else self.env.ref('project_extend.s_stage_3')
            next_stage_id = self.env.ref('project_extend.ns_stage_4') if task.assurance_id.type == 'non_soumise' else self.env.ref('project_extend.s_stage_4')
            if task.stage_id and task.stage_id == current_stage_id:
                date_last_stage_update = task.date_last_stage_update
                today = datetime.today()
                if (today - date_last_stage_update).days >= 30:
                    task.stage_id = next_stage_id

    @api.model
    def _attente_remboursement_cron_test(self):
        tasks = self.env['project.task'].search([])
        for task in tasks:
            current_stage_id = self.env.ref('project_extend.ns_stage_3') if task.assurance_id.type == 'non_soumise' else self.env.ref('project_extend.s_stage_3')
            next_stage_id = self.env.ref('project_extend.ns_stage_4') if task.assurance_id.type == 'non_soumise' else self.env.ref('project_extend.s_stage_4')
            if task.stage_id and task.stage_id == current_stage_id:
                date_last_stage_update = task.date_last_stage_update
                today = datetime.today()
                seconds = (today - date_last_stage_update).seconds
                minutes = seconds / 60
                if minutes >= 2:
                    task.stage_id = next_stage_id

    def write(self, vals):
        if vals.get('stage_id'):
            stage_id = self.env['project.task.type'].browse(vals['stage_id'])
            self.sudo().activity_schedule(
                 activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                 summary=stage_id.name + ' ' + self.partner_id.name,
                 user_id=self.user_id.id)
            project_non_soumise_id = self.env.ref('project_extend.project_non_soumise')
            project_soumise_id = self.env.ref('project_extend.project_soumise')
            accorde_stage_id = self.env.ref('project_extend.s_stage_6')
            ns_stage_2_id = self.env.ref('project_extend.ns_stage_2')
            if self.project_id == project_soumise_id and stage_id == accorde_stage_id:
                task_id = self.env['project.task'].create({
                    'project_id': project_non_soumise_id.id,
                    'name': self.partner_id.name + ' ' + self.assurance_id.name,
                    'partner_id': self.partner_id.id,
                    'stage_id': ns_stage_2_id.id,
                    'accorde_task_id': self.id
                })
                task_id.activity_schedule(
                 activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                 summary=stage_id.name + ' ' + self.partner_id.name,
                 user_id=self.user_id.id)
        return super(ProjectTask, self).write(vals)
