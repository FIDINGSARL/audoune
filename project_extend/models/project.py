# -*- encoding: utf-8 -*-

from odoo import models,fields, api
from datetime import datetime


class ProjectTask(models.Model):
    _inherit = 'project.task'

    pec_id = fields.Many2one('paiement.pec.client', string="Prise en charge")
    assurance_id = fields.Many2one('pec.assurance', related='pec_id.assurance_id', string="Assurance")

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
