from odoo import api, fields, models, _
import time
import csv
from odoo.modules import get_module_path
from odoo.exceptions import UserError
import copy
from io import StringIO
import base64
import odoo.tools

import logging
_logger = logging.getLogger(__name__)


class dummy_account_move_wizard(models.TransientModel):
    _name = 'vit.dummy_account_move'

    tmp_dir = '/tmp/'
    

    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    debit_account_id = fields.Many2one(comodel_name="account.account", string="Debit Account")
    credit_account_id = fields.Many2one(comodel_name="account.account", string="Credit Account")
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal")
    number_of_record = fields.Integer("Number of Records to generate")

    total_records = fields.Integer("Total Records", readonly=True)
    total_durations = fields.Float("Duration (s)", readonly=True)


    @api.multi
    def confirm_button(self):
        start = time.time()

        cr = self.env.cr
        sql = 'select vit_create_dummy_account_move(%s,%s,%s,%s, %s)'

        cr.execute(sql, (self.company_id.id, self.debit_account_id.id, self.credit_account_id.id, self.journal_id.id, self.number_of_record ))

        end = time.time()
        self.total_durations = end-start         
        return {
            'name': "Create dummy Complete, total %s seconds" % self.total_durations,
            'type': 'ir.actions.act_window',
            'res_model': 'vit.dummy_account_move',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
    