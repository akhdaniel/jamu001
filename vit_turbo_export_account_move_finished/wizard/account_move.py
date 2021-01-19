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


class export_account_move_wizard(models.TransientModel):
    _name = 'vit.export_account_move'

    tmp_dir = '/tmp/'
    
    date_from = fields.Datetime("Date From", required=True, default=fields.Datetime.now )
    date_to = fields.Datetime("Date To", required=True, default=fields.Datetime.now )
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner")
    state = fields.Selection(
        required=True,
        string='State',
        default='posted',
        selection=[('draft', 'Unposted'), ('posted', 'Posted')]
    )
    

    export_file = fields.Binary(string="Export File",  )
    export_filename = fields.Char(string="Export File",  )


    total_records = fields.Integer("Total Records", readonly=True)
    total_durations = fields.Float("Duration (s)", readonly=True)

   
    @api.multi
    def confirm_button(self):
        start = time.time()

        cr = self.env.cr

        sql = """\COPY (
                (	select am.date, am.id, am.name, am.ref, am.journal_id,
                    null as account_id, null as debit, null as credit, null as account, null as account_code, null as partner_name, null as partner_id
                    from account_move as am 
                    join account_move_line as aml on aml.move_id = am.id
                    join account_account as aa on aml.account_id = aa.id
                    join res_partner as par on aml.partner_id = par.id
                    where am.state='posted'
                    and am.date between '%s' and '%s'
                    order by am.date
                )
                UNION (
                    select am.date, am.id, null, null, null,
                    aml.account_id, aml.debit, aml.credit,
                    aa.name, aa.code,
                    par.name, par.id
                    from account_move as am 
                    join account_move_line as aml on aml.move_id = am.id
                    join account_account as aa on aml.account_id = aa.id
                    join res_partner as par on aml.partner_id = par.id
                    
                    where am.state='posted'
                    and am.date between '%s' and '%s'
                    order by am.date
                )
                
                order by date, id                
            ) TO '/tmp/export.csv' WITH (FORMAT CSV, HEADER TRUE, FORCE_QUOTE *)
        """ % (self.date_from, self.date_to, self.date_from, self.date_to)

        #------- psql dgn \copy command
        cmd = ['psql']
        cmd.append('--command='+sql)
        cmd.append( cr.dbname )
        odoo.tools.exec_pg_command(*cmd)

        # file terdowbnload ke local forlder odoo : /tmp/namafile
        fo = open('/tmp/export.csv', "rb")
        self.export_file = base64.b64encode( fo.read() )
        fo.close()
        self.export_filename = '/tmp/export.csv'

        end = time.time()
        self.total_durations = end-start         
        return {
            'name': "Export Complete, total %s seconds" % self.total_durations,
            'type': 'ir.actions.act_window',
            'res_model': 'vit.export_account_move',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
    