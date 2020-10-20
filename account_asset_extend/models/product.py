# -*- coding: utf-8 -*-
import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

from odoo.tools.translate import _
import math


class ProductTemplate(models.Model):
    _inherit = "product.template"

    company_id = fields.Many2one('res.company', string=u'Société', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'product.template'))
