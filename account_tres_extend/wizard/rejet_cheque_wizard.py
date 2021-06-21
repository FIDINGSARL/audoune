# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RejetChequeWizard(models.TransientModel):
    _inherit = "rejet.cheque.wizard"

    motif = fields.Many2one('rejet.cheque.motif', "Motif")

    def reject_action(self):
        cheque = self.env[self._context.get('active_model')].search([('id', '=', self._context.get('active_id'))])
        cheque.open_reject_wizard(self.in_relevet, self.date_rejet)
        cheque.activity_schedule(
            activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
            summary='Motif du rejet du chèque %s du patient %s est : %s' % (cheque.name, cheque.client.name, self.motif.name),
            user_id=self.env.user.id)
        judiciaire_project_id = self.env.ref('project_extend.project_procedure_judiciare')
        task_id = self.env['project.task'].create({
            'name': "Procédure du chèque numéro %s du client %s issue du motif : %s" % (cheque.name, cheque.client.name, self.motif.name),
            'project_id': judiciaire_project_id.id,
            'stage_id': self.env.ref('project_extend.pj_stage_1').id
        })


class RejetChequeMotif(models.Model):
    _name = "rejet.cheque.motif"

    name = fields.Char('Motif')
